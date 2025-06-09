#! /usr/bin/env python

# python m2m_download.py --region CU -h 11 -v 9 --dataset landsat_ba_tile_c2 --acq-date "2022-10-01,2022-12-31" -u tjhawbaker --password blah_blah_blah -d .

##########################################
## Valid Landsat datasets
## ['landsat_ot_c2_l1',
##  'landsat_ot_c2_l2',
##  'landsat_etm_c2_l1',
##  'landsat_etm_c2_l2',
##  'landsat_tm_c2_l1',
##  'landsat_tm_c2_l2',
##  'landsat_ard_tile_c2',
##  'landsat_dswe_tile_c2',
##  'landsat_ba_tile_c2',
##  'landsat_fsca_tile_c2',
##  'landsat_fsca_tile_stat_c2']
##
## Sentinel 2A dataset: 'sentinel_2a'
##########################################

login_token='UBFOvHpcmewTpVh4f!U6!c_iH8p4mwwGS7wCdTxAkMfJpIOd70S7XA@5MQWPwId8'
"""
Search and download M2M data, skip those already downloaded
"""

import os
import sys
import re
import requests
import json
import getpass
import urllib3
import time
import datetime
import logging
import traceback
import multiprocessing
from argparse import ArgumentParser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
FORMAT = '%(asctime)-15s ' \
         '%(name)-15s ' \
         '%(levelname)-8s ' \
         '%(message)s '
formatter = logging.Formatter(FORMAT)
stream.setFormatter(formatter)
logger.addHandler(stream)


class M2MError(Exception):
    pass


class DDSError(Exception):
    pass


class M2M(object):
    """
    Web-Service interface for EarthExplorer JSON Machine-to-Machine API

    https://m2m.cr.usgs.gov/api/docs/json/

    """
    
    

    def __init__(self, instance='ops'):
        url_lookup = dict(
            ops     = 'https://m2m.cr.usgs.gov/api/api/json/stable/',
            devmast = 'https://m2mdevmast.cr.usgs.gov/api/api/json/stable/',
            devsys  = 'https://m2mdev.cr.usgs.gov/devsys/api/api/json/stable/'
        )
        self.baseurl = url_lookup.get(instance)
        ## TODO - add MODIS and VIIRS

        # Product codes for the C2 ARD Tile Bundles
        # The scene-based products have two possible codes, one for on-prem
        # and one for on the cloud. For each ID, the download-options endpoint
        # will tell you which productId is valid, using the "available":true
        # field. We will specify both product codes. For the ARD Tiles, there
        # is only one code, so we will just use a dummy/invalid 'D000' that
        # won't ever be valid or used.
        self.product_codes = dict(
            landsat_tm_c2_l1=("D688", "D690"),
            landsat_etm_c2_l1=("D688", "D690"),
            landsat_ot_c2_l1=("D688", "D690"),
            landsat_tm_c2_l2=("D692", "D694"),
            landsat_etm_c2_l2=("D692", "D694"),
            landsat_ot_c2_l2=("D692", "D694"),
            landsat_ard_tile_c2={
                'SR': "D773",
                'TOA': "D775",
                'ST': "D774",
                'BT': "D776",
                'QA': "D777",
                'META': "D772"},
            landsat_dswe_tile_c2=("D000", "D788"),
            landsat_ba_tile_c2=("D000", "D784"),
            landsat_fsca_tile_c2=("D000", "D792"),
            landsat_fsca_tile_stat_c2=("D000", "D796"),
            sentinel_2a=("D000", "D557"),
            modis_mod09a1_v61=("D000", "D557"),
            modis_myd09a1_v61=("D000", "D557"),
            modis_mod09ga_v61=("D000", "D557"),
            modis_myd09ga_v61=("D000", "D557"),
)

        # Landsat Scene filters
        self.path_filter_id = dict(
            landsat_tm_c2_l1="5e83d0a017869321",
            landsat_etm_c2_l1="5e83d0d0a996690d",
            landsat_ot_c2_l1="5e81f14f8faf8048",
            landsat_tm_c2_l2="5e83d119a7bb2df1",
            landsat_etm_c2_l2="5e83d12a85c68941",
            landsat_ot_c2_l2="5e83d14fb9436d88")
        self.row_filter_id = dict(
            landsat_tm_c2_l1="5e83d0a0f068314e",
            landsat_etm_c2_l1="5e83d0d05ec3c916",
            landsat_ot_c2_l1="5e81f14f8d2a7c24",
            landsat_tm_c2_l2="5e83d1191d93d422",
            landsat_etm_c2_l2="5e83d12a86c531b9",
            landsat_ot_c2_l2="5e83d14ff1eda1b8")
        self.land_satellite_filter_id = dict(
            landsat_tm_c2_l1="5e83d0a072ef8b3f",
            landsat_ot_c2_l1="61af93b8fad2acf5",
            landsat_tm_c2_l2="5e83d119ec912f46",
            landsat_ot_c2_l2="61b0ca3aec6387e5")
        self.land_cloud_cover_filter_id = dict(
            landsat_tm_c2_l1="5f6aa1544fb24d4e",
            landsat_etm_c2_l1="5f6aa1792786a363",
            landsat_ot_c2_l1="5f6aa1a4e0985d4c",
            landsat_tm_c2_l2="5f6a715e654f6a9",
            landsat_etm_c2_l2="5f6a709195093287",
            landsat_ot_c2_l2="5f6a6f4a564f7484")

        # ARD Tile filters
        self.ard_region_filter_id = dict(
            landsat_ard_tile_c2="60fabf689767f137",
            landsat_dswe_tile_c2="6182717769cdbf49",
            landsat_ba_tile_c2="6183d3218e59dd06",
            landsat_fsca_tile_c2="618533b6ba46a347",
            landsat_fsca_tile_stat_c2="61979926e9ed7a92")
        self.ard_htile_filter_id = dict(
            landsat_ard_tile_c2="60fabf683e8957ca",
            landsat_dswe_tile_c2="6182717754c4ba2b",
            landsat_ba_tile_c2="6183d32138f962e3",
            landsat_fsca_tile_c2="618533b62b6213a7",
            landsat_fsca_tile_stat_c2="61979926660504ff")
        self.ard_vtile_filter_id = dict(
            landsat_ard_tile_c2="60fabf68a4fb8ff9",
            landsat_dswe_tile_c2="618271776640e10b",
            landsat_ba_tile_c2="6183d321c4a6fd67",
            landsat_fsca_tile_c2="618533b6763ab6ea",
            landsat_fsca_tile_stat_c2="6197992669094e66")
        self.ard_sensor_filter_id = dict(
            landsat_ard_tile_c2="60fabf6810783d37",
            landsat_dswe_tile_c2="61827177e711118b",
            landsat_ba_tile_c2="6183d32142bce78f",
            landsat_fsca_tile_c2="618533b6c2d0f60e")
        self.ard_satellite_filter_id = dict(
            landsat_ard_tile_c2="60fabf68dce2badd",
            landsat_dswe_tile_c2="6182717722c519c2",
            landsat_ba_tile_c2="6183d321a596f015",
            landsat_fsca_tile_c2="618533b6cf159c35")
        self.ard_production_date_filter_id = dict(
            landsat_ard_tile_c2="60fabf686abb6abf",
            landsat_dswe_tile_c2="618271779883310d",
            landsat_ba_tile_c2="6183d3216647e656",
            landsat_fsca_tile_c2="618533b68f9f4d61",
            landsat_fsca_tile_stat_c2="61979926ab310b9c")
        self.ard_cloud_cover_filter_id = dict(
            landsat_ard_tile_c2="60fabf689e9c00a6",
            landsat_dswe_tile_c2="61827177f71b9ebb",
            landsat_ba_tile_c2="6183d3219f34ec04",
            landsat_fsca_tile_c2="618533b6e5c97fb8")

        # Sentinel-2 filters
        self.s2_tile_number_filter_id = dict(
            sentinel_2a="5e83a42cc36e732d")
        self.s2_platform_filter_id = dict(
            sentinel_2a="5e83a42c8f7042bb")

    def accumulate_errors(self, response: requests.models.Response) -> dict:
        """
        Determine if errors are present in the response.  Assign an arbitrary
        level to each type of error.  The highest level error will take
        precedence when raising an exception.  All errors are logged.
        """

        errors = dict()
        server_exception = "M2M Server Exception"
        api_exception    = "M2M API Exception"

        code = response.status_code
        reason = response.reason

        # InventoryConnectionException
        if code >= 500:
            msg = "{0}: \n\t{1}: \n\t{2}".format(server_exception, code, reason)
            logger.error(msg)
            errors['Level-1'] = msg

        elif code >= 400:
            msg = "{0}: \n\t{1}: \n\t{2}".format(api_exception, code, reason)
            logger.error(msg)
            errors['Level-2'] = msg

        try:
            data = response.json()

        # LTAError
        except ValueError as e:
            msg = "{0}:\n\tUnable to parse JSON response.\n\t{1}:\n\t{2}".format(api_exception, e, traceback.format_exc())
            logger.error(msg)
            errors['Level-3'] = msg
            data = {'data': None}

        # LTAError
        err_code = data.get('errorCode', None)
        err_msg  = data.get('errorMessage', None)

        if err_code or err_msg:
            msg = "{0}: \n\t{1}: {2}".format(api_exception, err_code, err_msg)
            logger.error(msg)
            errors['Level-4'] = msg

        # LTAError
        if 'data' not in data.keys():
            msg = "{0}: \n\tNo data found in response".format(api_exception)
            logger.error(msg)
            errors['Level-5'] = msg

        return errors

    def raise_error(self, errors: dict) -> None:
        """
        Raise the appropriate exception with message if an error was found
        in the response
        """
        levels = range(5, 0, -1)
        for level in levels:
            msg = errors.get('Level-{}'.format(level), None)
            if msg:
                if level > 1:
                    raise M2MError(msg)

    def _parse(self, response):
        """
        Attempt to parse the JSON response, which always contains additional
        information that we might not always want to look at (except on error)

        :param response: requests.models.Response
        :return: dict
        """
        self.raise_error(self.accumulate_errors(response))
        data = response.json()
        logger.debug('RESPONSE {}'.format(data))
        return data

    def _api_request(self, verb, resource, data, headers=None):
        if not self.baseurl: raise ValueError("Base URL is not set. Please provide a valid base URL.")
        url = self.baseurl + resource
        data_ = {k: v if k != 'token' else 'xxxxx' for k, v in data.items()}
        logger.debug('POST {} {}'.format(url, data_))
        response = getattr(requests, verb)(url, headers=headers,
                                           data=json.dumps(data))
        return self._parse(response)

    def login(self, username=None, token=None, **kwargs):
        # if password is None:
        #     password = getpass.getpass('Password (%s): ' % username)
        with open('credentials.json','r') as file:
            credentials = json.load(file)
        username = credentials['username']
        # password = credentials['password']
        token = credentials['token']
        payload = {"username": username, "token": token}
        return self._api_request("post", "login-token", payload).get('data')

    def scene_search(self, headers, data):
        return self._api_request("post", "scene-search",  \
                                 data, headers).get('data')

    def product_lookup(self, dataset, products):
        """
        Match the dataset/product with the M2M download-options code
        """
        lookup = self.product_codes
        if dataset.lower() == 'landsat_ard_tile_c2':
            if products:
                products = products.split(',')
                products = [lookup['landsat_ard_tile_c2'][p] for p in products]
            else:
                # request SR by default
                products = [lookup['landsat_ard_tile_c2']['SR']]
        else:
            products = list(lookup.get(dataset.lower()))
        return products

    def download_options(self, headers, entity_ids, dataset, products):
        params = {
            'entityIds': entity_ids,
            'datasetName': dataset
        }
        resp = self._api_request("post", "download-options", params, headers)
        codes = self.product_lookup(dataset, products)
        product_info = filter(lambda i: i['productCode'] in codes and i['available'], resp.get('data'))
        return [(p.get('entityId'), p.get('id')) for p in product_info]

    def download_retrieve(self, headers, label):
        """
        docs:
        https://m2m.cr.usgs.gov/api/docs/reference/#download-retrieve

        Make a request to the M2M download-retrieve endpoint.  This will return
        all available and previous requests, but not completed downloads.  ESPA
        must utilize this endpoint to retrieve downloads for data that required
        staging prior to being made available.  Otherwise, repeat attempts to
        download-request for the same scene will continuously return the URL as
        'preparing' with the 'data-staging' address.

        Args:
            headers
            entity_ids
            label
        Returns:
            List[Tuple[urls, entityIds]]
        """
        params = {'downloadApplication': 'M2M', 'label': label}
        resp = self._api_request("post", "download-retrieve", params, headers)
        return resp

    def download_request(self, headers, entity_ids, download_ids, label):
        params = {
            'downloads': [
                {'entityId': e,
                 'productId': i}
                for e, i in zip(entity_ids, download_ids)
            ],
            'downloadApplication': 'M2M',
            'label': label
        }
        resp = self._api_request("post", "download-request", params, headers)

        return resp

    def get_download_urls(self, headers, entity_ids, product_ids, label):
        """
        Use download-request and download-retrieve to get available data URLs
        """
        url_mapping = dict()
        request_resp = self.download_request(headers, entity_ids, product_ids,
                                             label)['data']

        request_avail  = request_resp.get('availableDownloads', [])
        # request_prep = request_resp.get('preparingDownloads', [])
        req_duplicates = request_resp.get('duplicateProducts', [])

        if isinstance(req_duplicates, list):
            duplicates = []
        else:
            duplicates = set(req_duplicates.values())

        for label_ in duplicates:
            retrieve_resp = self.download_retrieve(headers, label_)['data']
            retrieve_avail = retrieve_resp.get('available', [])
            retrieve_requested = retrieve_resp.get('requested', [])
            # M2M URL statusCodes that represent URLs we can use immediately
            # A = Available
            # P = Proxied
            # D = Downloading
            found = list(filter(lambda x: x['statusCode'] in ('A', 'P', 'D'), retrieve_avail + retrieve_requested))
            logger.debug('Retrieved {}/{} downloads using duplicateProducts label {}'.format(len(found), len(entity_ids), label_))
            for item in found:
                key = item['entityId']
                if key not in url_mapping:
                    url_mapping[key] = item['url']
            if len(url_mapping) >= len(entity_ids):
                logger.debug('All {} URLs retrieved!'.format(len(entity_ids)))
                return url_mapping

        if len(request_avail) == len(entity_ids):
            wait = None  # don't need to wait, all requested URLs are ready
        else:
            wait = 30  # seconds

##        while (len(url_mapping) < len(entity_ids)):
        if wait:
            logger.info("Waiting for {} seconds before attempting to retrieve available downloads".format(wait))
            time.sleep(wait)
        
        retr_resp = self.download_retrieve(headers, label)['data']
        retrieve_avail = retr_resp.get('available', [])
        retrieve_requested   = retr_resp.get('requested', [])

        found = list(filter(lambda x: x['statusCode'] in ('A', 'P', 'D'), retrieve_avail + retrieve_requested))
        for item in found:
            if len(found) > 1:
                # multiple products for this dataset
                key = item['entityId']
                key2 = item['productCode']
                key = key + '_' + key2
            else:
                # only one product with this dataset
                key = item['entityId']
            if key not in url_mapping:
                url_mapping[key] = item['url']

        return url_mapping

    @staticmethod
    def additionalCriteriaValues(self, dataset=None, h=None, v=None, p=None,
        r=None, s=None, sc=None, sat=None, rg=None, pd=None, cc=None, lcc=None,
        
        tile_number=None, platform=None):

        k = 'metadataFilter'
        additional = {k: {"filterType": "and", "childFilters": []}}

        # ARD Tile filters
        if (dataset == 'landsat_ard_tile_c2' or
            dataset == 'landsat_dswe_tile_c2' or
            dataset == 'landsat_ba_tile_c2' or
            dataset == 'landsat_fsca_tile_c2' or
            dataset == 'landsat_fsca_tile_stat_c2'):
            if rg: # Tile region
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.ard_region_filter_id[dataset], "value": rg})
            if h: # horizontal tile number
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.ard_htile_filter_id[dataset], "firstValue": h, "secondValue": h})
            if v: # vertical tile number
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.ard_vtile_filter_id[dataset], "firstValue": v, "secondValue": v})

        if (dataset == 'landsat_ard_tile_c2' or
            dataset == 'landsat_dswe_tile_c2' or
            dataset == 'landsat_ba_tile_c2' or
            dataset == 'landsat_fsca_tile_c2'):
            if s:  # sensor
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.ard_sensor_filter_id[dataset], "value": s})
            if sc:  # spacecraft
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.ard_satellite_filter_id[dataset], "value": sc})
            if pd:  # production date
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.ard_production_date_filter_id[dataset], "firstValue": pd, "secondValue": pd})
            if cc:  # <= cloud cover
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.ard_cloud_cover_filter_id[dataset], "value": cc})

        # Landsat scene filters
        if (dataset == 'landsat_tm_c2_l1' or
            dataset == 'landsat_etm_c2_l1' or
            dataset == 'landsat_ot_c2_l1' or
            dataset == 'landsat_tm_c2_l2' or
            dataset == 'landsat_etm_c2_l2' or
            dataset == 'landsat_ot_c2_l2'):
            if p:  # path
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.path_filter_id[dataset], "firstValue": p, "secondValue": p})
            if r:  # row
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.row_filter_id[dataset], "firstValue": r, "secondValue": r})
            if sat:  # satellite
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.land_satellite_filter_id[dataset], "value": sat})
            if lcc:  # landsat cloud cover (scenes)
                additional[k]['childFilters'].append({"filterType": "between", "filterId": self.land_cloud_cover_filter_id[dataset], "firstValue": 0, "secondValue": lcc})

        # Sentinel-2 tile filter
        if (dataset == 'sentinel_2a'):
            if tile_number:
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.s2_tile_number_filter_id[dataset], "value": tile_number, "operand": "like"})
    
            if platform:  ## SENTINEL-2A and SENTINEL-2B
                additional[k]['childFilters'].append({"filterType": "value", "filterId": self.s2_platform_filter_id[dataset], "value": platform})

        return additional

    @staticmethod
    def temporalCriteria(ad):
        # Support the acquisition date. If only one date is supplied, then
        # use it for the starting and ending date range. Otherwise, the first
        # date is the starting date and the second date is the ending date.
        # The date range must be separated by a comma.
        dates = ad.split(',')
        sd, ed = dates if len(dates) == 2 else dates * 2
        return {"acquisitionFilter": {"start": sd, "end": ed}}
### End M2M Class


def handle_redirect(x):
    head = requests.head(x, timeout=60)
    location = head.headers.get('Location')
    if location is None:
        msg = 'Error retrieving redirect URL for {}'.format(x)
        logger.error(msg)
        raise DDSError(msg)
    
    base_url = x.split('/download-staging')[0]
    redirect_url = base_url + location
    return redirect_url


def download_url(x):
    # We need to get the redirect URL first
    pattern = r'(L[E|T|O|C]\d{2}_L\d{1}\w{2}_\d{6}_\d{8}_\d{8}_\d{2}_\w\d(\.tar)?)|(L\w{1}\d{2}_\w{2}_\d{6}_\d{8}_\d{8}_\d{2}_\d{2}*.tar)|(L1C_.*\.zip)|(S2A_.*\.zip)'
    fileurl, directory = x[0], x[1]
    bytes_recv = 0
    bytes_in_mb = 1024*1024

    if 'download-staging' in fileurl:
        fileurl_ = handle_redirect(fileurl)
    else:
        fileurl_ = fileurl

    head = requests.head(fileurl_, timeout=60)

    content_disposition = head.headers.get('Content-Disposition')
    location = head.headers.get('Location')
    
    try:
        if content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"').strip("'")
        elif location:
            filename = re.search(pattern, location).group()
        elif 'landsatlook.usgs.gov' in fileurl_:
            filename = fileurl_.split('&requestSignature')[0]
            filename = filename.split('landsat_product_id=')[1]
        else:
            raise DDSError
    except Exception:
        msg = 'Unable to determine filename from headers (content-disposition and/or location) in {}'.format(fileurl_)
        logger.error(msg)
        raise DDSError(msg)
    
    # Add extension for Landsat C2
    if os.path.splitext(filename)[-1] == '':
        filename = filename + '.tar'

    local_fname = os.path.join(directory, filename)
    if os.path.exists(local_fname):
        logger.warning('Already exists - skipping: %s \n' % local_fname)
        return
    try:
        file_size = None
        if 'Content-Length' in head.headers:
            file_size = int(head.headers['Content-Length'])
            
            if os.path.exists(local_fname + '.part'):
                bytes_recv = os.path.getsize(local_fname + '.part')

            logger.info("Downloading\n\t{}\n\tto\n\t{} ... \n".format(fileurl_, local_fname))
            resume_header = {'Range': 'bytes=%d-' % bytes_recv}
            sock = requests.get(fileurl_, headers=resume_header, timeout=6000,
                                stream=True, verify=False, allow_redirects=True)

            start = time.time()
            with open(local_fname + '.part', 'ab') as f:
                
                for block in sock.iter_content(chunk_size=bytes_in_mb):
                    if block:
                        f.write(block)
                        bytes_recv += len(block)
            ns = time.time() - start
            mb = bytes_recv/float(bytes_in_mb)
            logger.info("Complete - %s (%3.2f (MB) in %3.2f (s), or  %3.2f (MB/s)) \n" % (filename, mb, ns, mb/ns))

            if bytes_recv >= file_size:
                os.rename(local_fname + '.part', local_fname) 
        
        else:  # content-length unknown - cloud-hosted?
            if os.path.exists(local_fname + '.part'):
                # We aren't gonna deal with this if we don't know
                # the final file size
                os.remove(local_fname + '.part')
            logger.info("Downloading\n\t{}\n\tto\n\t{} ... \n".format(fileurl_, local_fname))
            sock = requests.get(fileurl_, timeout=6000, stream=True, verify=False, allow_redirects=True)
            start = time.time()
            with open(local_fname, 'ab') as f:
                for block in sock.iter_content(chunk_size=bytes_in_mb):
                    if block:
                        f.write(block)
                        bytes_recv += len(block)
            ns = time.time() - start
            mb = bytes_recv/float(bytes_in_mb)
            logger.info("Complete - %s (%3.2f (MB) in %3.2f (s), or  %3.2f (MB/s)) \n" % (filename, mb, ns, mb/ns))
    except Exception as e:
        try:
            # Need to remove the *.tar/*.zip/*.tar.gz
            # if we aren't writing to *.part
            os.remove(local_fname)
        except FileNotFoundError:
            pass
        raise

def download_url_wrapper(x):
    try:
        download_url(x)
    except Exception as e:
        logger.warning('\n\n *** Failed download %s: %s \n' % (x[0], str(e)))


def chunkify(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def get_product_ids(results):
    return [x['displayId'] for x in results], [y['entityId'] for y in results]


def clean(param):
    if isinstance(param, str):
        return param.strip('"').strip("'")
    else:
        return param


def download_files(directory, h=None, v=None, p=None, r=None, username=None, token=None,
                   dataset=None, tile_number=None, sensor=None, spacecraft=None,
                   satellite=None, region=None, N=15000, products=None,
                   acq_date=None, prod_date=None, cloud_cover=None,
                   land_cloud_cover=None, platform=None, threads=12,
                   search_only=False, instance='ops', debug=False):
    """
    Search for and download files to local directory

        Args:
            directory: Relative path to local directory (will be created)
            h: ARD Tile Grid Horizontal [Optional]
            v: ARD Tile Grid Vertical [Optional]
            p: Landsat WRS2 path [Optional]
            r: Landsat WRS2 row [Optional]
            username: ERS Username (with full M2M download access) [Optional]
            password: ERS Password [Optional]
            dataset: EarthExplorer Catalog datasetName
                     [e.g. landsat_ard_tile_c2 or sentinel_2a]
            tile_number: SENTINEL-2 tile number
            sensor: ARD Tile Satellite instrument [All, OLI_TIRS, ETM, TM]
            spacecraft: ARD Tile Satellite platform [LANDSAT_4,
                        LANDSAT_5, LANDSAT_7, LANDSAT_8, LANDSAT_9]
            satellite: Scene Satellite instrument [All, 4, 5, 7, 8, 9]
            region: ARD Tile Grid Region [AK, CU, HI]
            N: Maximum number of search results to return
            products: Comma-delimited list of download products as a single
                      string [e.g 'TOA,BT,SR,ST,QA,META']
            acq_date: Landsat acquisition date [Format: %Y-%m-%d]. If
                      two dates are supplied, then search for a range of
                      dates. Dates need to be separated by a comma.
            prod_date: ARD Tile production date [Format: %Y-%m-%d]
            cloud_cover: ARD Tile cloud cover <= [10, 20, ... 90, 100]
            land_cloud_cover: Landsat cloud cover <= Value
            platform: Sentinel platforms [All, SENTINEL-2A, SENTINEL-2B]
            threads: Number of download threads to launch in parallel
            search_only: Boolean, if true only show results, don't download
            instance: What instance of M2M to use (devsys, devmast, ops)
            debug (bool): If True, set log level to DEBUG
    """
    if debug:
        stream.setLevel(logging.DEBUG)

    if not directory and not search_only:
        logger.error('Must specify download directory')
        sys.exit(0)

    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    m2m = M2M(instance)

    full_token = m2m.login(username=username, token=token) # or input('Enter ERS username: '))
    header = {'X-Auth-Token': full_token}
    
    scene_filter = dict(
        metadataFilter    = None,
        cloudCoverFilter  = {"max": 100, "min": 0},
        acquisitionFilter = None
    )
    
    if any([h, v, p, r, sensor, spacecraft, region, prod_date, cloud_cover,
            land_cloud_cover, tile_number, platform]):
        scene_filter.update(m2m.additionalCriteriaValues(m2m, dataset=dataset,
             h=h, v=v, p=p, r=r, s=sensor, sc=spacecraft, sat=satellite,
             rg=region, pd=clean(prod_date), cc=cloud_cover,
             lcc=land_cloud_cover, tile_number=tile_number, platform=platform))
    
    if acq_date:
        scene_filter.update(m2m.temporalCriteria(ad=clean(acq_date)))

    search = dict(
        datasetName = dataset, 
        maxResults  = "{}".format(N),
        sceneFilter = scene_filter)
    
    results = m2m.scene_search(header, search)
    n_results = results.get('totalHits')
    display_ids, entity_ids = get_product_ids(results.get('results'))

    logger.info('Total search results: %d \n' % n_results)

    if len(display_ids) < 1:
        logger.warning('No results found!')
        sys.exit(0)

    if not search_only:
        download_info = m2m.download_options(header, entity_ids, dataset,
                                             products)
        e_ids = [x[0] for x in download_info]
        d_ids = [x[1] for x in download_info]
        work_todo = list()

        # Make the initial download request, then sleep for 10 seconds
        # to allow data to stage
        # List[url]
        now = datetime.datetime.strftime(datetime.datetime.now(),
                                         '%Y%m%d%H%M%S')
        label = f'{dataset}-{now}'
        # req_avail = m2m.download_request(header, e_ids, d_ids, label)
        # dict entityId: URL
        urls = m2m.get_download_urls(header, e_ids, d_ids, label)
        work_todo.extend([(x, directory) for x in urls.values()])

        pool = multiprocessing.Pool(threads)
        pool.map_async(download_url_wrapper, work_todo).get(6000)
        pool.close()
        pool.join()

    else:
        now = datetime.datetime.now()
        name = datetime.datetime.strftime(now, '%Y-%m-%d_%H:%M:%S')
        name = 'results_{}.txt'.format(name)
        text_output = os.path.join(directory, name)
        with open(text_output, 'w') as f:
            for i in display_ids:
                f.write('{}\n'.format(i))
        logger.info('SEARCH RESULTS: ')
        logger.info('{}'.format(display_ids))
        logger.info('Writing results to {}'.format(text_output))

    return None


def build_command_line_arguments():
    description = __doc__
    parser = ArgumentParser(description=description, add_help=False)
    req_parser = parser.add_argument_group('required arguments')
    parser.add_argument('--help', action='help',
        help='show this help message and exit')
    req_parser.add_argument('-d', '--directory', type=str, dest='directory',
        help='Relative path to download all data')
    req_parser.add_argument('-u', '--username', type=str, dest='username',
        default=None, help='ERS Username (with full M2M download access)')
    req_parser.add_argument('-tkn', '--token', type=str, dest='token',
        default=None, help='ERS Token (with full M2M download access)')    
    parser.add_argument('-t', '--threads', type=int, dest='threads', default=12,
        help='Number of parallel download threads [Default: 50]')
    parser.add_argument('-m', '--max', type=int, dest='N', default=50000,
        help='Maximum number of Tile results to return [Default: 50000]')
    parser.add_argument('-p', '--path', type=int, dest='p', default=None,
        help='WRS-2 Path [Default: All]')
    parser.add_argument('-r', '--row', type=int, dest='r', default=None,
        help='WRS-2 Row [Default: All]')
    parser.add_argument('-h', '--horizontal', type=int, dest='h', default=None,
        help='ARD Tile Grid Horizontal [Default: All]')
    parser.add_argument('-v', '--vertical', type=int, dest='v', default=None,
        help='ARD Tile Grid Vertical [Default: All]')
    parser.add_argument('--region', type=str, dest='region', default=None,
        choices=['CU', 'AK', 'HI'], help='ARD Tile Grid Region [Default: All]')
    parser.add_argument('--tile-number', type=str, dest='tile_number',
        default=None,
        help='Sentinel-2 Tile Number (e.g. T19TDK) [Default: All]')
    parser.add_argument('--platform', type=str, dest='platform',
        default=None,
        help='Sentinel-2 Platform (e.g SENTINEL-2A, SENTINEL-2B) '
             '[Default: All]')
    parser.add_argument('-s', '--sensor', type=str, dest='sensor', default=None,
        choices=['All', 'OLI_TIRS', 'ETM', 'TM'],
        help='ARD Tile Sensor Identifier [Default: All]')
    parser.add_argument('--spacecraft', dest='spacecraft', default=None,
        choices=[f'LANDSAT_{x}' for x in (4, 5, 7, 8, 9)],
        help='ARD Tile Spacecraft Identifier [Default: All]')
    parser.add_argument('--satellite', dest='satellite', default=None,
        choices=['4', '5', '7', '8', '9'],
        help='Scene Spacecraft Identifier [Default: All]')
    parser.add_argument('--products', dest='products', default=None,
        help='M2M ARD product names (e.g. "SR,TOA,BT,ST,QA,META")')
    req_parser.add_argument('--dataset', type=str, dest='dataset',
        required=True, help='EE Catalog dataset [e.g. sentinel_2a]')
    parser.add_argument('--acq-date', type=str, dest='acq_date', default=None,
        help='Search Date Acquired (YYYY-MM-DD). If two dates are specified '
             'then a date range is used to search. The dates need to be '
             'separated by a comma (YYYY-MM-DD,YYYY-MM-DD).')
    parser.add_argument('--prod-date', type=str, dest='prod_date', default=None,
        help='ARD Tile Production Date (YYYY/MM/DD)')
    parser.add_argument('-cc', '--cloud-cover', type=int, dest='cloud_cover',
        choices=[10,20,30,40,50,60,70,80,90,100],
        default=None, help='ARD Tile Cloud Cover <= {cc_val} [Default: All]')
    parser.add_argument('-lcc', '--land-cloud-cover', type=int,
        dest='land_cloud_cover', default=None,
        help='Scene-based Cloud Cover (0-100) <= {cc_val} [Default: All]')
    parser.add_argument('--search-only', action='store_true',
        dest='search_only', help='Only return search results, do not download')
    parser.add_argument('--instance', type=str, dest='instance',
        choices=['devsys', 'devmast', 'ops'], default='ops',
        help='Which instance of M2M to use (devsys, devmast, ops)')
    parser.add_argument('--debug', action='store_true', default=False,
        help='Set log level to DEBUG (Shows M2M POST requests/responses)')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    download_files(**vars(build_command_line_arguments()))
