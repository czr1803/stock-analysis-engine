"""
Helper for getting data from redis

Debug redis calls with:

::

    export DEBUG_REDIS=1

    # to show debug, trace logging please export ``SHARED_LOG_CFG``
    # to a debug logger json file. To turn on debugging for this
    # library, you can export this variable to the repo's
    # included file with the command:
    export SHARED_LOG_CFG=/opt/sa/analysis_engine/log/debug-logging.json

"""

import json
import zlib
import redis
import analysis_engine.consts as ae_consts
import analysis_engine.build_result as build_result
import spylunking.log.setup_logging as log_utils

log = log_utils.build_colorized_logger(name=__name__)


def get_data_from_redis_key(
        label=None,
        client=None,
        host=None,
        port=None,
        password=None,
        db=None,
        key=None,
        expire=None,
        decompress_df=False,
        serializer='json',
        encoding='utf-8'):
    """get_data_from_redis_key

    :param label: log tracking label
    :param client: initialized redis client
    :param host: not used yet - redis host
    :param port: not used yet - redis port
    :param password: not used yet - redis password
    :param db: not used yet - redis db
    :param key: not used yet - redis key
    :param expire: not used yet - redis expire
    :param decompress_df: used for decompressing
        ``pandas.DataFrame`` automatically
    :param serializer: not used yet - support for future
                       pickle objects in redis
    :param encoding: format of the encoded key in redis
    """

    decoded_data = None
    data = None

    rec = {
        'data': data
    }
    res = build_result.build_result(
        status=ae_consts.NOT_RUN,
        err=None,
        rec=rec)

    log_id = label if label else 'get-data'

    try:

        use_client = client
        if not use_client:
            log.debug(
                '{} get key={} new client={}:{}@{}'.format(
                    log_id,
                    key,
                    host,
                    port,
                    db))
            use_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db)
        else:
            log.debug(
                '{} get key={} client'.format(
                    log_id,
                    key))
        # create Redis client if not set

        # https://redis-py.readthedocs.io/en/latest/index.html#redis.StrictRedis.get  # noqa
        raw_data = use_client.get(
            name=key)

        if raw_data:

            if decompress_df:
                try:
                    data = zlib.decompress(
                        raw_data).decode(
                            encoding)
                    rec['data'] = json.loads(data)

                    return build_result.build_result(
                        status=ae_consts.SUCCESS,
                        err=None,
                        rec=rec)
                except Exception as f:
                    if (
                            'while decompressing data: '
                            'incorrect header check') in str(f):
                        data = None
                        log.critical(
                            'unable to decompress_df in redis_key={} '
                            'ex={}'.format(
                                key,
                                f))
                    else:
                        log.error(
                            'failed decompress_df in redis_key={} '
                            'ex={}'.format(
                                key,
                                f))
                        raise f
            # allow decompression failure to fallback to previous method

            if not data:
                log.debug(
                    '{} decoding key={} encoding={}'.format(
                        log_id,
                        key,
                        encoding))
                decoded_data = raw_data.decode(encoding)

                log.debug(
                    '{} deserial key={} serializer={}'.format(
                        log_id,
                        key,
                        serializer))

                if serializer == 'json':
                    data = json.loads(decoded_data)
                elif serializer == 'df':
                    data = decoded_data
                else:
                    data = decoded_data

                if data:
                    if ae_consts.ev('DEBUG_REDIS', '0') == '1':
                        log.info(
                            '{} - found key={} data={}'.format(
                                log_id,
                                key,
                                ae_consts.ppj(data)))
                    else:
                        log.debug(
                            '{} - found key={}'.format(
                                log_id,
                                key))
            # log snippet - if data

            rec['data'] = data

            return build_result.build_result(
                status=ae_consts.SUCCESS,
                err=None,
                rec=rec)
        else:
            log.debug(
                '{} no data key={}'.format(
                    log_id,
                    key))
            return build_result.build_result(
                status=ae_consts.SUCCESS,
                err=None,
                rec=rec)
    except Exception as e:
        err = (
            '{} failed - redis get from decoded={} data={} '
            'key={} ex={}'.format(
                log_id,
                decoded_data,
                data,
                key,
                e))
        log.error(err)
        res = build_result.build_result(
            status=ae_consts.ERR,
            err=err,
            rec=rec)
    # end of try/ex for getting redis data

    return res
# end of get_data_from_redis_key
