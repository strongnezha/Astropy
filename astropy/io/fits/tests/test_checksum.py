import warnings

import numpy as np

from ...io import fits
from . import FitsTestCase

from ...test.helper import pytest


class TestChecksumFunctions(FitsTestCase):

    def setup(self):
        super(TestChecksumFunctions, self).setup()
        self._oldfilters = warnings.filters[:]
        warnings.filterwarnings(
            'error',
             message='Checksum verification failed')
        warnings.filterwarnings(
            'error',
            message='Datasum verification failed')

    def teardown(self):
        super(TestChecksumFunctions, self).teardown()
        warnings.filters = self._oldfilters

    def test_sample_file(self):
        hdul = fits.open(self.data('checksum.fits'), checksum=True)
        hdul.close()

    def test_image_create(self):
        n = np.arange(100)
        hdu = fits.PrimaryHDU(n)
        hdu.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_nonstandard_checksum(self):
        hdu = fits.PrimaryHDU(np.arange(10.**6))
        hdu.writeto(self.temp('tmp.fits'), clobber=True,
                    checksum='nonstandard')
        del hdu
        hdul = fits.open(self.temp('tmp.fits'), checksum='nonstandard')

    def test_scaled_data(self):
        hdul = fits.open(self.data('scale.fits'))
        hdul[0].scale('int16', 'old')
        hdul.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul1 = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()
        hdul1.close()

    def test_uint16_data(self):
        hdul = fits.open(self.data('o4sp040b0_raw.fits'), uint=True)
        hdul.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul1 = fits.open(self.temp('tmp.fits'), uint=True, checksum=True)
        hdul.close()
        hdul1.close()

    def test_groups_hdu_data(self):
        imdata = np.arange(100.)
        imdata.shape=(10,1,1,2,5)
        pdata1 = np.arange(10)+0.1
        pdata2 = 42
        x = fits.hdu.groups.GroupData(imdata, parnames=['abc', 'xyz'],
                                      pardata=[pdata1, pdata2], bitpix=-32)
        hdu = fits.GroupsHDU(x)
        hdu.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul1 = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul1.close()

    def test_binary_table_data(self):
        a1 = np.array(['NGC1001','NGC1002','NGC1003'])
        a2 = np.array([11.1,12.3,15.2])
        col1 = fits.Column(name='target', format='20A', array=a1)
        col2 = fits.Column(name='V_mag', format='E', array=a2)
        cols = fits.ColDefs([col1, col2])
        tbhdu = fits.new_table(cols)
        tbhdu.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_variable_length_table_data(self):
        c1 = fits.Column(name='var', format='PJ()',
            array=np.array([[45., 56], np.array([11, 12, 13])], 'O'))
        c2 = fits.Column(name='xyz', format='2I', array=[[11, 3], [12, 4]])
        tbhdu = fits.new_table([c1, c2])
        tbhdu.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_ascii_table_data(self):
        a1 = np.array(['abc', 'def'])
        r1 = np.array([11., 12.])
        c1 = fits.Column(name='abc', format='A3', array=a1)
        c2 = fits.Column(name='def', format='E', array=r1, bscale=2.3,
                         bzero=0.6)
        c3 = fits.Column(name='t1', format='I', array=[91,92,93])
        x = fits.ColDefs([c1, c2, c3], tbtype='TableHDU')
        hdu = fits.new_table(x, tbtype='TableHDU')
        hdu.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_compressed_image_data(self):
        hdul = fits.open(self.data('comp.fits'))
        hdul.writeto(self.temp('tmp.fits'), clobber=True, checksum=True)
        hdul1=fits.open(self.temp('tmp.fits'), checksum=True)
        hdul1.close()
        hdul.close()

    def test_compressed_image_data_int16(self):
        n = np.arange(100, dtype='int16')
        hdu = fits.ImageHDU(n)
        comp_hdu = fits.CompImageHDU(hdu.data, hdu.header)
        comp_hdu.writeto(self.temp('tmp.fits'), checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_compressed_image_data_float32(self):
        n = np.arange(100, dtype='float32')
        comp_hdu = fits.CompImageHDU(n)
        comp_hdu.writeto(self.temp('tmp.fits'), checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        hdul.close()

    def test_open_with_no_keywords(self):
        hdul = fits.open(self.data('arange.fits'), checksum=True)
        hdul.close()

    def test_append(self):
        hdul = fits.open(self.data('tb.fits'))
        hdul.writeto(self.temp('tmp.fits'), clobber=True)
        n = np.arange(100)
        fits.append(self.temp('tmp.fits'), n, checksum=True)
        hdul.close()
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        assert hdul[0]._checksum == None
        hdul.close()

    def test_writeto_convenience(self):
        n = np.arange(100)
        fits.writeto(self.temp('tmp.fits'), n, clobber=True, checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        self._check_checksums(hdul[0])
        hdul.close()

    def test_hdu_writeto(self):
        n = np.arange(100, dtype='int16')
        hdu = fits.ImageHDU(n)
        hdu.writeto(self.temp('tmp.fits'), checksum=True)
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        self._check_checksums(hdul[0])
        hdul.close()

    def test_datasum_only(self):
        n = np.arange(100, dtype='int16')
        hdu = fits.ImageHDU(n)
        hdu.writeto(self.temp('tmp.fits'), clobber=True, checksum='datasum')
        hdul = fits.open(self.temp('tmp.fits'), checksum=True)
        self._check_checksums(hdul[0])
        hdul.close()

    def _check_checksums(self, hdu):
        if not (hasattr(hdu, '_datasum') and hdu._datasum):
            pytest.fail(msg='Missing DATASUM keyword')

        if not (hasattr(hdu, '_checksum') and hdu._checksum):
            pytest.fail(msg='Missing CHECKSUM keyword')

        if not (hasattr(hdu, '_datasum_comment') and hdu._datasum_comment):
            pytest.fail(msg='Missing DATASUM Card comment')

        if not (hasattr(hdu, '_checksum_comment') and hdu._checksum_comment):
            pytest.fail(msg='Missing CHECKSUM Card comment')


