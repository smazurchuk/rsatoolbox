#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tests for comparing RDMs
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.spatial.distance import pdist, squareform
import pyrsa.rdm as rsr
import pyrsa as rsa


class TestCompareRDM(unittest.TestCase):

    def setUp(self):
        dissimilarities1 = np.random.rand(1, 15)
        des1 = {'session': 0, 'subj': 0}
        self.test_rdm1 = rsa.rdm.RDMs(
            dissimilarities=dissimilarities1,
            dissimilarity_measure='test',
            descriptors=des1)
        dissimilarities2 = np.random.rand(3, 15)
        des2 = {'session': 0, 'subj': 0}
        self.test_rdm2 = rsa.rdm.RDMs(
            dissimilarities=dissimilarities2,
            dissimilarity_measure='test',
            descriptors=des2
            )
        dissimilarities3 = np.random.rand(7, 15)
        des2 = {'session': 0, 'subj': 0}
        self.test_rdm3 = rsa.rdm.RDMs(
            dissimilarities=dissimilarities3,
            dissimilarity_measure='test',
            descriptors=des2
            )

    def test_compare_cosine(self):
        from pyrsa.rdm.compare import compare_cosine
        result = compare_cosine(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_cosine(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_compare_cosine_cov(self):
        from pyrsa.rdm.compare import compare_cosine_cov_weighted
        result = compare_cosine_cov_weighted(self.test_rdm1,
                                             self.test_rdm1,
                                             sigma_k=np.eye(6))
        assert_array_almost_equal(result, 1)
        result = compare_cosine_cov_weighted(self.test_rdm1,
                                             self.test_rdm2,
                                             sigma_k=np.eye(6))
        assert np.all(result < 1)

    def test_compare_cosine_loop(self):
        from pyrsa.rdm.compare import compare_cosine
        result = compare_cosine(self.test_rdm2, self.test_rdm3)
        assert result.shape[0] == 3
        assert result.shape[1] == 7
        result_loop = np.zeros_like(result)
        d1 = self.test_rdm2.get_vectors()
        d2 = self.test_rdm3.get_vectors()
        for i in range(result_loop.shape[0]):
            for j in range(result_loop.shape[1]):
                result_loop[i, j] = (np.sum(d1[i] * d2[j])
                                     / np.sqrt(np.sum(d1[i] * d1[i]))
                                     / np.sqrt(np.sum(d2[j] * d2[j])))
        assert_array_almost_equal(result, result_loop)

    def test_compare_correlation(self):
        from pyrsa.rdm.compare import compare_correlation
        result = compare_correlation(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_correlation(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_compare_correlation_cov(self):
        from pyrsa.rdm.compare import compare_correlation_cov_weighted
        result = compare_correlation_cov_weighted(self.test_rdm1,
                                                  self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_correlation_cov_weighted(self.test_rdm1,
                                                  self.test_rdm2)
        assert np.all(result < 1)

    def test_compare_correlation_cov_sk(self):
        from pyrsa.rdm.compare import compare_correlation_cov_weighted
        result = compare_correlation_cov_weighted(self.test_rdm1,
                                                  self.test_rdm1,
                                                  sigma_k=np.eye(6))
        assert_array_almost_equal(result, 1)
        result = compare_correlation_cov_weighted(self.test_rdm1,
                                                  self.test_rdm2,
                                                  sigma_k=np.eye(6))
        assert np.all(result < 1)

    def test_compare_corr_loop(self):
        from pyrsa.rdm.compare import compare_correlation
        result = compare_correlation(self.test_rdm2, self.test_rdm3)
        assert result.shape[0] == 3
        assert result.shape[1] == 7
        result_loop = np.zeros_like(result)
        d1 = self.test_rdm2.get_vectors()
        d2 = self.test_rdm3.get_vectors()
        d1 = d1 - np.mean(d1, 1, keepdims=True)
        d2 = d2 - np.mean(d2, 1, keepdims=True)
        for i in range(result_loop.shape[0]):
            for j in range(result_loop.shape[1]):
                result_loop[i, j] = (np.sum(d1[i] * d2[j])
                                     / np.sqrt(np.sum(d1[i] * d1[i]))
                                     / np.sqrt(np.sum(d2[j] * d2[j])))
        assert_array_almost_equal(result, result_loop)

    def test_compare_spearman(self):
        from pyrsa.rdm.compare import compare_spearman
        result = compare_spearman(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_spearman(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_compare_rho_a(self):
        from pyrsa.rdm.compare import compare_rho_a
        result = compare_rho_a(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_rho_a(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_spearman_equal_scipy(self):
        from pyrsa.rdm.compare import _parse_input_rdms
        from pyrsa.rdm.compare import _all_combinations
        import scipy.stats
        from pyrsa.rdm.compare import compare_spearman

        def _spearman_r(vector1, vector2):
            """computes the spearman rank correlation between two vectors

            Args:
                vector1 (numpy.ndarray):
                    first vector
                vector1 (numpy.ndarray):
                    second vector
            Returns:
                corr (float):
                    spearman r

            """
            corr = scipy.stats.spearmanr(vector1, vector2).correlation
            return corr
        vector1, vector2 = _parse_input_rdms(self.test_rdm1, self.test_rdm2)
        sim = _all_combinations(vector1, vector2, _spearman_r)
        result = sim
        result2 = compare_spearman(self.test_rdm1, self.test_rdm2)
        assert_array_almost_equal(result, result2)

    def test_compare_kendall_tau(self):
        from pyrsa.rdm.compare import compare_kendall_tau
        result = compare_kendall_tau(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_kendall_tau(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_compare_kendall_tau_a(self):
        from pyrsa.rdm.compare import compare_kendall_tau_a
        result = compare_kendall_tau_a(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare_kendall_tau_a(self.test_rdm1, self.test_rdm2)
        assert np.all(result < 1)

    def test_compare(self):
        from pyrsa.rdm.compare import compare
        result = compare(self.test_rdm1, self.test_rdm1)
        assert_array_almost_equal(result, 1)
        result = compare(self.test_rdm1, self.test_rdm2, method='corr')
        result = compare(self.test_rdm1, self.test_rdm2, method='corr_cov')
        result = compare(self.test_rdm1, self.test_rdm2, method='spearman')
        result = compare(self.test_rdm1, self.test_rdm2, method='cosine')
        result = compare(self.test_rdm1, self.test_rdm2, method='cosine_cov')
        result = compare(self.test_rdm1, self.test_rdm2, method='kendall')