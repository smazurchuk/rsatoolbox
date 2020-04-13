#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 12:42:06 2020

@author: heiko
"""

from collections.abc import Iterable
import numpy as np


def get_cov_from_residuals(residuals, df=None):
    """
    computes an optimal shrinkage estimate of the precision matrix from 
    the residuals as described by Ledoit and Wolfe (2004): "A well-conditioned
    estimator for large-dimensional covariance matrices"

    Args:
        residuals(numpy.ndarray or list of these): n_obs x n_channels matrix
            of residuals
        df(int or list of int): degrees of freedom for covariance estimation
            defaults to n_obs-1, should be corrected for 

    Returns:
        numpy.ndarray (or list): sigma_p: covariance matrix over channels

    """
    if not isinstance(residuals, np.ndarray) or len(residuals.shape) > 2:
        s_shrink = []
        for i in range(len(residuals)):
            if df is None:
                s_shrink.append(get_cov_from_residuals(residuals[i]))
            elif isinstance(df, Iterable):
                s_shrink.append(get_cov_from_residuals(residuals[i], df[i]))
            else:
                s_shrink.append(get_cov_from_residuals(residuals[i], df))
    else:  
        if df is None:
            df = residuals.shape[0] - 1 
        residuals = residuals - np.mean(residuals, axis=0, keepdims=True)
        xt_x = np.einsum('ij, ik-> ijk', residuals, residuals)
        s = np.sum(xt_x, axis=0) / xt_x.shape[0]
        m = np.sum(np.diag(s)) / s.shape[0]
        d2 = np.sum((s - m * np.eye(s.shape[0])) ** 2)
        b2 = np.sum((xt_x - s) ** 2) / xt_x.shape[0] / xt_x.shape[0]
        b2 = min(d2, b2)
        s_shrink = b2 / d2 * m * np.eye(s.shape[0]) \
            + (d2-b2) / d2 * s
        s_shrink = s_shrink * xt_x.shape[0] / df
    return s_shrink


def get_prec_from_residuals(residuals, df=None):
    """
    computes an optimal shrinkage estimate of the precision matrix from 
    the residuals as described by Ledoit and Wolfe (2004): "A well-conditioned
    estimator for large-dimensional covariance matrices"

    Args:
        residuals(numpy.ndarray or list of these): n_obs x n_channels matrix
            of residuals
        df(int or list of int): degrees of freedom for covariance estimation
            defaults to n_obs-1, should be corrected for 

    Returns:
        numpy.ndarray (or list): sigma_p: covariance matrix over channels

    """
    cov = get_cov_from_residuals(residuals=residuals, df=df)
    if not isinstance(cov, np.ndarray) or len(cov.shape) > 2:
        for i in range(len(cov)):
            cov[i] = np.linalg.inv(cov[i])
    else:
        cov = np.linalg.inv(cov)
    return cov
    