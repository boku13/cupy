from math import sqrt, pi

import cupy
import cupyx.scipy.signal as signal
from cupy import testing
from cupy.testing import assert_array_almost_equal, assert_allclose

import numpy as np

import pytest
from pytest import raises as assert_raises


@testing.with_requires("scipy")
class TestFreqz:

    def test_ticket1441(self):
        """Regression test for ticket 1441."""
        # Because freqz previously used arange instead of linspace,
        # when N was large, it would return one more point than
        # requested.
        N = 100000
        w, h = signal.freqz([1.0], worN=N)
        assert w.shape == (N,)

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_basic(self, xp, scp):
        w, h = scp.signal.freqz([1.0], worN=8)
        return w, h

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_basic_2(self, xp, scp):
        w, h = scp.signal.freqz([1.0], worN=9)
        return w, h

    def test_basic_3(self):
        for a in [1, cupy.ones(2)]:
            w, h = signal.freqz(cupy.ones(2), a, worN=0)
            assert w.shape == (0,)
            assert h.shape == (0,)
            assert h.dtype == cupy.dtype('complex128')

    def test_basic_4(self):
        xp = cupy
        t = xp.linspace(0, 1, 4, endpoint=False)
        for b, a, h_whole in zip(
                ([1., 0, 0, 0], xp.sin(2 * xp.pi * t)),
                ([1., 0, 0, 0], [0.5, 0, 0, 0]),
                ([1., 1., 1., 1.], [0, -4j, 0, 4j])):
            w, h = signal.freqz(b, a, worN=4, whole=True)

            expected_w = xp.linspace(0, 2 * xp.pi, 4, endpoint=False)
            assert_array_almost_equal(w, expected_w)
            assert_array_almost_equal(h, h_whole)

            # simultaneously check int-like support
            w, h = signal.freqz(b, a, worN=xp.int32(4), whole=True)
            assert_array_almost_equal(w, expected_w)
            assert_array_almost_equal(h, h_whole)

            w, h = signal.freqz(b, a, worN=w, whole=True)
            assert_array_almost_equal(w, expected_w)
            assert_array_almost_equal(h, h_whole)

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_basic_whole(self, xp, scp):
        w, h = scp.signal.freqz([1.0], worN=8, whole=True)
        return w, h

    @pytest.mark.skip(reason='plot')
    def test_plot(self):

        def plot(w, h):
            assert_array_almost_equal(w, pi * cupy.arange(8.0) / 8)
            assert_array_almost_equal(h, cupy.ones(8))

        assert_raises(ZeroDivisionError, signal.freqz, [1.0], worN=8,
                      plot=lambda w, h: 1 / 0)
        freqz([1.0], worN=8, plot=plot)

    def test_fft_wrapping(self):
        # Some simple real FIR filters
        bs = list()  # filters
        as_ = list()
        hs_whole = list()
        hs_half = list()
        # 3 taps
        t = cupy.linspace(0, 1, 3, endpoint=False)
        bs.append(cupy.sin(2 * pi * t))
        as_.append(3.)
        hs_whole.append([0, -0.5j, 0.5j])
        hs_half.append([0, sqrt(1./12.), -0.5j])
        # 4 taps
        t = cupy.linspace(0, 1, 4, endpoint=False)
        bs.append(cupy.sin(2 * pi * t))
        as_.append(0.5)
        hs_whole.append([0, -4j, 0, 4j])
        hs_half.append([0, sqrt(8), -4j, -sqrt(8)])
        del t

        for ii, b in enumerate(bs):
            # whole
            a = as_[ii]
            expected_w = cupy.linspace(0, 2 * pi, len(b), endpoint=False)
            w, h = signal.freqz(b, a, worN=expected_w, whole=True)  # polyval
            err_msg = f'b = {b}, a={a}'
            assert_array_almost_equal(w, expected_w, err_msg=err_msg)
            assert_array_almost_equal(h, hs_whole[ii], err_msg=err_msg)

            w, h = signal.freqz(b, a, worN=len(b), whole=True)  # FFT
            assert_array_almost_equal(w, expected_w, err_msg=err_msg)
            assert_array_almost_equal(h, hs_whole[ii], err_msg=err_msg)

            # non-whole
            expected_w = cupy.linspace(0, pi, len(b), endpoint=False)
            w, h = signal.freqz(b, a, worN=expected_w, whole=False)  # polyval
            assert_array_almost_equal(w, expected_w, err_msg=err_msg)
            assert_array_almost_equal(h, hs_half[ii], err_msg=err_msg)

            w, h = signal.freqz(b, a, worN=len(b), whole=False)  # FFT
            assert_array_almost_equal(w, expected_w, err_msg=err_msg)
            assert_array_almost_equal(h, hs_half[ii], err_msg=err_msg)

    def test_fft_wrapping_2(self):
        # some random FIR filters (real + complex)
        # assume polyval is accurate
        rng = cupy.random.RandomState(0)
        for ii in range(2, 10):  # number of taps
            b = rng.randn(ii)
            for kk in range(2):
                a = rng.randn(1) if kk == 0 else rng.randn(3)
                for jj in range(2):
                    if jj == 1:
                        b = b + rng.randn(ii) * 1j
                    # whole
                    expected_w = cupy.linspace(0, 2 * pi, ii, endpoint=False)
                    w, expected_h = signal.freqz(
                        b, a, worN=expected_w, whole=True)
                    assert_array_almost_equal(w, expected_w)

                    w, h = signal.freqz(b, a, worN=ii, whole=True)
                    assert_array_almost_equal(w, expected_w)
                    assert_array_almost_equal(h, expected_h)

                    # half
                    expected_w = cupy.linspace(0, pi, ii, endpoint=False)
                    w, expected_h = signal.freqz(
                        b, a, worN=expected_w, whole=False)
                    assert_array_almost_equal(w, expected_w)

                    w, h = signal.freqz(b, a, worN=ii, whole=False)
                    assert_array_almost_equal(w, expected_w)
                    assert_array_almost_equal(h, expected_h)

    @pytest.mark.parametrize('whole', [True, False])
    @pytest.mark.parametrize('worN', [16, 17, np.linspace(0, 1, 10), np.array([])])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_broadcasting1(self, xp, scp, whole, worN):
        # Test broadcasting with worN an integer or a 1-D array,
        # b and a are n-dimensional arrays.
        np.random.seed(123)
        b = np.random.rand(3, 5, 1)
        a = np.random.rand(2, 1)
        if xp == cupy:
            a = cupy.asarray(a)
            b = cupy.asarray(b)

            if isinstance(worN, np.ndarray):
                worN = cupy.asarray(worN)

        w, h = scp.signal.freqz(b, a, worN=worN, whole=whole)
        return w, h

    @pytest.mark.parametrize('whole', [True, False])
    @pytest.mark.parametrize('worN', [16, 17, np.linspace(0, 1, 10)])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_broadcasting2(self, xp, scp, whole, worN):
        # Test broadcasting with worN an integer or a 1-D array,
        # b is an n-dimensional array, and a is left at the default value.
        np.random.seed(123)
        b = np.random.rand(3, 5, 1)

        if xp == cupy:
            b = cupy.asarray(b)
            if isinstance(worN, np.ndarray):
                worN = cupy.asarray(worN)

        w, h = scp.signal.freqz(b, worN=worN, whole=whole)

        # with CuPy, division by a changes the strides: fft_func(b, n=n_fft, axis=0)[:N] / a
        # fft_func(...)[:N] is F-ordered, but the ratio is C-ordered.
        # With Numpy, it remains F-ordered. Make a copy for the comparison.
        h = h.copy(order='F')

        return w, h

    @pytest.mark.parametrize('whole', [True, False])
    @pytest.mark.parametrize('worN', [16, np.linspace(0, 1, 16)])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_broadcasting3(self, xp, scp, whole, worN):
        # Test broadcasting where b.shape[-1] is the same length
        # as worN, and a is left at the default value.
        np.random.seed(123)
        N = 16
        b = np.random.rand(3, N)     # XXX: N is worN or len(worN) !

        if xp == cupy:
            b = cupy.asarray(b)

        w, h = scp.signal.freqz(b, worN=worN, whole=whole)
        assert w.size == N
        return w, h

    @pytest.mark.parametrize('whole', [True, False])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_broadcasting4(self, xp, scp, whole):
        # Test broadcasting with worN a 2-D array.
        np.random.seed(123)
        b = np.random.rand(4, 2, 1, 1)
        a = np.random.rand(5, 2, 1, 1)

        wh = []

        for worN in [np.random.rand(6, 7), np.empty((6, 0))]:
            if xp == cupy:
                a = cupy.asarray(a)
                b = cupy.asarray(b)
                worN = cupy.asarray(worN)

            w, h = scp.signal.freqz(b, a, worN=worN, whole=whole)
            wh.append(w)
            wh.append(h)
        return wh

    def test_backward_compat(self):
        # For backward compatibility, test if None act as a wrapper for default
        w1, h1 = signal.freqz([1.0], 1)
        w2, h2 = signal.freqz([1.0], 1, None)
        assert_array_almost_equal(w1, w2)
        assert_array_almost_equal(h1, h2)

    def test_fs_param(self):
        fs = 900
        b = [0.039479155677484369, 0.11843746703245311, 0.11843746703245311,
             0.039479155677484369]
        a = [1.0, -1.3199152021838287, 0.80341991081938424,
             -0.16767146321568049]

        # N = None, whole=False
        w1, h1 = signal.freqz(b, a, fs=fs)
        w2, h2 = signal.freqz(b, a)
        testing.assert_allclose(h1, h2)
        testing.assert_allclose(
            w1, cupy.linspace(0, fs/2, 512, endpoint=False))

        # N = None, whole=True
        w1, h1 = signal.freqz(b, a, whole=True, fs=fs)
        w2, h2 = signal.freqz(b, a, whole=True)
        testing.assert_allclose(h1, h2)
        testing.assert_allclose(w1, cupy.linspace(0, fs, 512, endpoint=False))

        # N = 5, whole=False
        w1, h1 = signal.freqz(b, a, 5, fs=fs)
        w2, h2 = signal.freqz(b, a, 5)
        testing.assert_allclose(h1, h2)
        testing.assert_allclose(w1, cupy.linspace(0, fs/2, 5, endpoint=False))

        # N = 5, whole=True
        w1, h1 = signal.freqz(b, a, 5, whole=True, fs=fs)
        w2, h2 = signal.freqz(b, a, 5, whole=True)
        testing.assert_allclose(h1, h2)
        testing.assert_allclose(w1, cupy.linspace(0, fs, 5, endpoint=False))

        # w is an array_like
        for w in ([123], (123,), cupy.array([123]), (50, 123, 230),
                  cupy.array([50, 123, 230])):
            w1, h1 = signal.freqz(b, a, w, fs=fs)
            w2, h2 = signal.freqz(b, a, 2 * pi * cupy.array(w) / fs)
            testing.assert_allclose(h1, h2)
            testing.assert_allclose(w, w1)

    @pytest.mark.parametrize('N',
                             [7, cupy.int8(7), cupy.int16(7), cupy.int32(7),
                              cupy.int64(7), cupy.array(7),
                              8, cupy.int8(8), cupy.int16(8), cupy.int32(8),
                              cupy.int64(8), cupy.array(8)
                              ])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_w_or_N_types(self, xp, scp, N):
        # Measure at 7 (polyval) or 8 (fft) equally-spaced points

        if xp == np and isinstance(N, cupy.ndarray):
            N = N.get()

        w, h = scp.signal.freqz([1.0], worN=N)
        w1, h1 = scp.signal.freqz([1.0], worN=N, fs=100)

        return w, h, w1, h1

    @pytest.mark.parametrize('N',
                             [7, cupy.int8(7), cupy.int16(7), cupy.int32(7),
                              cupy.int64(7), cupy.array(7),
                              8, cupy.int8(8), cupy.int16(8), cupy.int32(8),
                              cupy.int64(8), cupy.array(8)
                              ])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_w_or_N_types_2(self, xp, scp, N):
        if xp == np and isinstance(N, cupy.ndarray):
            N = N.get()

        w, h = scp.signal.freqz([1.0], worN=N)
        return w, h

    @pytest.mark.parametrize("w", [8.0, 8.0 + 0j])
    @testing.numpy_cupy_allclose(scipy_name='scp')
    def test_w_or_N_types_3(self, xp, scp, w):
        # Measure at frequency 8 Hz
        # Only makes sense when fs is specified
        w, h = scp.signal.freqz([1.0], worN=w, fs=100)
        return w, h

    @pytest.mark.parametrize("worN", [8, 9])
    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_nyquist(self, xp, scp, worN):
        w, h = scp.signal.freqz([1.0], worN=worN, include_nyquist=True)
        return w, h

    @pytest.mark.parametrize("nyq", [True, False])
    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_nyquist_1(self, xp, scp, nyq):
        w, h = scp.signal.freqz([1.0], worN=8, whole=True, include_nyquist=nyq)
        return w, h

    @pytest.mark.parametrize("a", [1, cupy.ones(2)])
    def test_nyquist_2(self, a):
        w, h = signal.freqz(cupy.ones(2), a, worN=0, include_nyquist=True)
        assert w.shape == (0,)
        assert h.shape == (0,)
        assert h.dtype == cupy.dtype('complex128')


@testing.with_requires("scipy")
class TestFreqz_zpk:

    def test_ticket1441(self):
        """Regression test for ticket 1441."""
        # Because freqz previously used arange instead of linspace,
        # when N was large, it would return one more point than
        # requested.
        N = 100000
        w, h = signal.freqz_zpk([0.5], [0.5], 1.0, worN=N)
        assert w.shape == (N,)

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_basic(self, xp, scp):
        w, h = scp.signal.freqz_zpk([0.5], [0.5], 1.0, worN=8)
        return w, h

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_basic_whole(self, xp, scp):
        w, h = scp.signal.freqz_zpk([0.5], [0.5], 1.0, worN=8, whole=True)
        return w, h

    @pytest.mark.xfail(reason="implement cheby1")
    def test_vs_freqz(self):
        b, a = cheby1(4, 5, 0.5, analog=False, output='ba')
        z, p, k = cheby1(4, 5, 0.5, analog=False, output='zpk')

        w1, h1 = freqz(b, a)
        w2, h2 = signal.freqz_zpk(z, p, k)
        assert_allclose(w1, w2)
        assert_allclose(h1, h2, rtol=1e-6)

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_backward_compat(self, xp, scp):
        # For backward compatibility, test if None act as a wrapper for default
        w1, h1 = scp.signal.freqz_zpk([0.5], [0.5], 1.0)
        w2, h2 = scp.signal.freqz_zpk([0.5], [0.5], 1.0, None)
        return w1, h1, w2, h2

    def test_fs_param(self):
        fs = 900
        z = [-1, -1, -1]
        p = [0.4747869998473389+0.4752230717749344j, 0.37256600288916636,
             0.4747869998473389-0.4752230717749344j]
        k = 0.03934683014103762

        # N = None, whole=False
        w1, h1 = signal.freqz_zpk(z, p, k, whole=False, fs=fs)
        w2, h2 = signal.freqz_zpk(z, p, k, whole=False)
        assert_allclose(h1, h2)
        assert_allclose(w1, cupy.linspace(0, fs/2, 512, endpoint=False))

        # N = None, whole=True
        w1, h1 = signal.freqz_zpk(z, p, k, whole=True, fs=fs)
        w2, h2 = signal.freqz_zpk(z, p, k, whole=True)
        assert_allclose(h1, h2)
        assert_allclose(w1, cupy.linspace(0, fs, 512, endpoint=False))

        # N = 5, whole=False
        w1, h1 = signal.freqz_zpk(z, p, k, 5, fs=fs)
        w2, h2 = signal.freqz_zpk(z, p, k, 5)
        assert_allclose(h1, h2)
        assert_allclose(w1, cupy.linspace(0, fs/2, 5, endpoint=False))

        # N = 5, whole=True
        w1, h1 = signal.freqz_zpk(z, p, k, 5, whole=True, fs=fs)
        w2, h2 = signal.freqz_zpk(z, p, k, 5, whole=True)
        assert_allclose(h1, h2)
        assert_allclose(w1, cupy.linspace(0, fs, 5, endpoint=False))

        # w is an array_like
        for w in ([123], (123,), cupy.array([123]), (50, 123, 230),
                  cupy.array([50, 123, 230])):
            w1, h1 = signal.freqz_zpk(z, p, k, w, fs=fs)
            w2, h2 = signal.freqz_zpk(z, p, k, 2*pi*cupy.array(w)/fs)
            assert_allclose(h1, h2)
            assert_allclose(w, w1)

    def test_w_or_N_types(self):
        # Measure at 8 equally-spaced points
        for N in (8, cupy.int8(8), cupy.int16(8), cupy.int32(8), cupy.int64(8),
                  cupy.array(8)):

            w, h = signal.freqz_zpk([], [], 1, worN=N)
            assert_array_almost_equal(w, pi * cupy.arange(8) / 8.)
            assert_array_almost_equal(h, cupy.ones(8))

            w, h = signal.freqz_zpk([], [], 1, worN=N, fs=100)
            assert_array_almost_equal(
                w, cupy.linspace(0, 50, 8, endpoint=False))
            assert_array_almost_equal(h, cupy.ones(8))

        # Measure at frequency 8 Hz
        for w in (8.0, 8.0+0j):
            # Only makes sense when fs is specified
            w_out, h = signal.freqz_zpk([], [], 1, worN=w, fs=100)
            assert_array_almost_equal(w_out, [8])
            assert_array_almost_equal(h, [1])


@testing.with_requires("scipy")
class TestSOSFreqz:

    @pytest.mark.xfail(reason="TODO: implement butter et al")
    def test_sosfreqz_basic(self):
        # Compare the results of freqz and sosfreqz for a low order
        # Butterworth filter.

        N = 500

        b, a = butter(4, 0.2)
        sos = butter(4, 0.2, output='sos')
        w, h = freqz(b, a, worN=N)
        w2, h2 = sosfreqz(sos, worN=N)
        assert_equal(w2, w)
        assert_allclose(h2, h, rtol=1e-10, atol=1e-14)

        b, a = ellip(3, 1, 30, (0.2, 0.3), btype='bandpass')
        sos = ellip(3, 1, 30, (0.2, 0.3), btype='bandpass', output='sos')
        w, h = freqz(b, a, worN=N)
        w2, h2 = sosfreqz(sos, worN=N)
        assert_equal(w2, w)
        assert_allclose(h2, h, rtol=1e-10, atol=1e-14)
        # must have at least one section
        assert_raises(ValueError, sosfreqz, sos[:0])

    @pytest.mark.xfail(reason="TODO: implement butter et al")
    def test_sosfrez_design(self):
        # Compare sosfreqz output against expected values for different
        # filter types

        # from cheb2ord
        N, Wn = cheb2ord([0.1, 0.6], [0.2, 0.5], 3, 60)
        sos = cheby2(N, 60, Wn, 'stop', output='sos')
        w, h = sosfreqz(sos)
        h = np.abs(h)
        w /= np.pi
        assert_allclose(20 * np.log10(h[w <= 0.1]), 0, atol=3.01)
        assert_allclose(20 * np.log10(h[w >= 0.6]), 0., atol=3.01)
        assert_allclose(h[(w >= 0.2) & (w <= 0.5)], 0., atol=1e-3)  # <= -60 dB

        N, Wn = cheb2ord([0.1, 0.6], [0.2, 0.5], 3, 150)
        sos = cheby2(N, 150, Wn, 'stop', output='sos')
        w, h = sosfreqz(sos)
        dB = 20*np.log10(np.abs(h))
        w /= np.pi
        assert_allclose(dB[w <= 0.1], 0, atol=3.01)
        assert_allclose(dB[w >= 0.6], 0., atol=3.01)
        assert_array_less(dB[(w >= 0.2) & (w <= 0.5)], -149.9)

        # from cheb1ord
        N, Wn = cheb1ord(0.2, 0.3, 3, 40)
        sos = cheby1(N, 3, Wn, 'low', output='sos')
        w, h = sosfreqz(sos)
        h = np.abs(h)
        w /= np.pi
        assert_allclose(20 * np.log10(h[w <= 0.2]), 0, atol=3.01)
        assert_allclose(h[w >= 0.3], 0., atol=1e-2)  # <= -40 dB

        N, Wn = cheb1ord(0.2, 0.3, 1, 150)
        sos = cheby1(N, 1, Wn, 'low', output='sos')
        w, h = sosfreqz(sos)
        dB = 20*np.log10(np.abs(h))
        w /= np.pi
        assert_allclose(dB[w <= 0.2], 0, atol=1.01)
        assert_array_less(dB[w >= 0.3], -149.9)

        # adapted from ellipord
        N, Wn = ellipord(0.3, 0.2, 3, 60)
        sos = ellip(N, 0.3, 60, Wn, 'high', output='sos')
        w, h = sosfreqz(sos)
        h = np.abs(h)
        w /= np.pi
        assert_allclose(20 * np.log10(h[w >= 0.3]), 0, atol=3.01)
        assert_allclose(h[w <= 0.1], 0., atol=1.5e-3)  # <= -60 dB (approx)

        # adapted from buttord
        N, Wn = buttord([0.2, 0.5], [0.14, 0.6], 3, 40)
        sos = butter(N, Wn, 'band', output='sos')
        w, h = sosfreqz(sos)
        h = np.abs(h)
        w /= np.pi
        assert_allclose(h[w <= 0.14], 0., atol=1e-2)  # <= -40 dB
        assert_allclose(h[w >= 0.6], 0., atol=1e-2)  # <= -40 dB
        assert_allclose(20 * np.log10(h[(w >= 0.2) & (w <= 0.5)]),
                        0, atol=3.01)

        N, Wn = buttord([0.2, 0.5], [0.14, 0.6], 3, 100)
        sos = butter(N, Wn, 'band', output='sos')
        w, h = sosfreqz(sos)
        dB = 20*np.log10(np.maximum(np.abs(h), 1e-10))
        w /= np.pi
        assert_array_less(dB[(w > 0) & (w <= 0.14)], -99.9)
        assert_array_less(dB[w >= 0.6], -99.9)
        assert_allclose(dB[(w >= 0.2) & (w <= 0.5)], 0, atol=3.01)

    @pytest.mark.xfail(reason="TODO: implement ellip et al")
    def test_sosfreqz_design_ellip(self):
        N, Wn = ellipord(0.3, 0.1, 3, 60)
        sos = ellip(N, 0.3, 60, Wn, 'high', output='sos')
        w, h = sosfreqz(sos)
        h = np.abs(h)
        w /= np.pi
        assert_allclose(20 * np.log10(h[w >= 0.3]), 0, atol=3.01)
        assert_allclose(h[w <= 0.1], 0., atol=1.5e-3)  # <= -60 dB (approx)

        N, Wn = ellipord(0.3, 0.2, .5, 150)
        sos = ellip(N, .5, 150, Wn, 'high', output='sos')
        w, h = sosfreqz(sos)
        dB = 20*np.log10(np.maximum(np.abs(h), 1e-10))
        w /= np.pi
        assert_allclose(dB[w >= 0.3], 0, atol=.55)
        # Allow some numerical slop in the upper bound -150, so this is
        # a check that dB[w <= 0.2] is less than or almost equal to -150.
        assert dB[w <= 0.2].max() < -150*(1 - 1e-12)

    @testing.with_requires("mpmath > 0.10")
    def test_sos_freqz_against_mp(self):
        # Compare the result of sosfreqz applied to a high order Butterworth
        # filter against the result computed using mpmath.  (signal.freqz fails
        # miserably with such high order filters.)
        from . import mpsig
        N = 500
        order = 25
        Wn = 0.15
        with mpmath.workdps(80):
            z_mp, p_mp, k_mp = mpsig.butter_lp(order, Wn)
            w_mp, h_mp = mpsig.zpkfreqz(z_mp, p_mp, k_mp, N)
        w_mp = np.array([float(x) for x in w_mp])
        h_mp = np.array([complex(x) for x in h_mp])

        sos = butter(order, Wn, output='sos')
        w, h = sosfreqz(sos, worN=N)
        assert_allclose(w, w_mp, rtol=1e-12, atol=1e-14)
        assert_allclose(h, h_mp, rtol=1e-12, atol=1e-14)

    def _get_fs_sos(self):
        fs = 900
        sos = [[0.03934683014103762, 0.07869366028207524, 0.03934683014103762,
                1.0, -0.37256600288916636, 0.0],
               [1.0, 1.0, 0.0, 1.0, -0.9495739996946778, 0.45125966317124144]]
        return fs, sos            

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_fs_param(self, xp, scp):
        fs, sos = self._get_fs_sos()

        # N = None, whole=False
        w1, h1 = scp.signal.sosfreqz(sos, fs=fs)
        w2, h2 = scp.signal.sosfreqz(sos)
        return w1, h1, w2, h2

    @testing.numpy_cupy_allclose(scipy_name="scp", atol=1e-10)
    def test_fs_param_2(self, xp, scp):
        fs, sos = self._get_fs_sos()

        # N = None, whole=True
        w1, h1 = scp.signal.sosfreqz(sos, whole=True, fs=fs)
        w2, h2 = scp.signal.sosfreqz(sos, whole=True)
        return w1, h1, w2, h2

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_fs_param_3(self, xp, scp):
        fs, sos = self._get_fs_sos()
        # N = 5, whole=False
        w1, h1 = scp.signal.sosfreqz(sos, 5, fs=fs)
        w2, h2 = scp.signal.sosfreqz(sos, 5)
        return w1, h1, w2, h2

    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_fs_param_4(self, xp, scp):
        fs, sos = self._get_fs_sos()
        # N = 5, whole=True
        w1, h1 = scp.signal.sosfreqz(sos, 5, whole=True, fs=fs)
        w2, h2 = scp.signal.sosfreqz(sos, 5, whole=True)
        return w1, h1, w2, h2

    @pytest.mark.parametrize("w", [[123], (123,),
                                   np.array([123]), (50, 123, 230),
                                   np.array([50, 123, 230])])
    @testing.numpy_cupy_allclose(scipy_name="scp")
    def test_fs_param_5(self, xp, scp, w):
        fs, sos = self._get_fs_sos()

        if xp == cupy and isinstance(w, np.ndarray):
            w = cupy.asarray(w)

        # w is an array_like
        w1, h1 = scp.signal.sosfreqz(sos, w, fs=fs)
        w2, h2 = scp.signal.sosfreqz(sos, 2*pi*xp.array(w)/fs)
        return w1, h1, w2, h2

    def test_w_or_N_types(self):
        # Measure at 7 (polyval) or 8 (fft) equally-spaced points
        for N in (7, cupy.int8(7), cupy.int16(7), cupy.int32(7), cupy.int64(7),
             #     cupy.array(7),
                  8, cupy.int8(8), cupy.int16(8), cupy.int32(8), cupy.int64(8),
             #     cupy.array(8)
                 ):

            w, h = signal.sosfreqz([1, 0, 0, 1, 0, 0], worN=N)
            assert_array_almost_equal(w, pi * cupy.arange(N) / N)
            assert_array_almost_equal(h, cupy.ones(N))

            w, h = signal.sosfreqz([1, 0, 0, 1, 0, 0], worN=N, fs=100)
            assert_array_almost_equal(w, cupy.linspace(0, 50, N, endpoint=False))
            assert_array_almost_equal(h, cupy.ones(N))

        # Measure at frequency 8 Hz
        for w in (8.0, 8.0+0j):
            # Only makes sense when fs is specified
            w_out, h = signal.sosfreqz([1, 0, 0, 1, 0, 0], worN=w, fs=100)
            assert_array_almost_equal(w_out, [8])
            assert_array_almost_equal(h, [1])

