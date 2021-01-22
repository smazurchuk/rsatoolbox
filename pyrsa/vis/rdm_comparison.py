#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2020-09-17

@author: caiw
"""

from typing import Tuple, List, Union, Dict, Optional

from numpy import fill_diagonal, array
from matplotlib import pyplot, rcParams
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from scipy.spatial.distance import squareform

from pyrsa.rdm import RDMs
from pyrsa.util.matrix import square_category_binary_mask, square_between_category_binary_mask
from pyrsa.util.rdm_utils import category_condition_idxs


_Colour = Tuple[float, float, float]


_default_colour = "#107ab0"  # xkcd:nice blue
_default_cmap   = None


def rdm_comparison_scatterplot(rdms,
                               show_marginal_distributions: bool = True,
                               show_identity_line: bool = True,
                               highlight_category_selector: Union[str, List[int]] = None,
                               highlight_categories: List = None,
                               colors: Dict[str, _Colour] = None,
                               cmap = None,
                               axlim: Tuple[float, float] = None,
                               hist_bins: int = 30,
                               **scatter_kwargs,
                               ):
    """
    Plot dissimilarities for 2 or more RDMs

    Args:
        rdms (RDMs object or list-like of 2 RDMs objects):
            If one RDMs object supplied, each RDM within is compared against each other
            If two RDMs objects supplied (as list, tuple, etc.), each RDM in the first is compared against each RDM in the second
        show_marginal_distributions (bool):
            True (default): Show marginal distributions.
            False: Don't.
        show_identity_line (bool):
            True (default): Show identity line in each graph.
            False: Don't.
        highlight_category_selector (Optional. str or List[int]):
            EITHER: A RDMs.pattern_descriptor defining category labelling for conditions.
                OR: A list of ints providing category labels for each condition.
            If None or not supplied, no categories will be highlighted, in which case `highlight_categories` must also
            be None.
        highlight_categories (Optional. List):
            List of category labels to highlight. Must be compatible with `highlight_category_selector`.
            Colours within each and between each pair of categories will be highlighted.
        colors: (Optional. Dict):
            Dict mapping category labels to RGB 3-tuples of floats (values range 0–1).  Between-category colours will be
            interpolated midpoints between category colours.
            If None (the default), default colours will be selected.
            Only used if `highlight_categories` is not None.
        cmap: (Optional. matplotlib colormap)
            Specify matplotlib colormap for use in selecting category colours.
            If None (the default), default cmap will be used.
            Only used if `highlight_categories` is not None.
        axlim (Optional. Tuple[float, float]):
            Set the axis limits for the figure.
            If None or not supplied, axis limits will be automatically determined.
        hist_bins (int, default 30):
            The number of bins to use in the histogram.

    Returns:
        matplotlib.pyplot.Figure containing the scatter plot (not shown).

    """

    rdms_x, rdms_y = _handle_args_rdms(rdms)
    category_idxs: Optional[Dict[str, List[int]]] = _handle_args_highlight_categories(highlight_category_selector, highlight_categories, rdms_x)
    if cmap is None:
        cmap = _default_cmap
    if colors is None and highlight_categories is not None:
        # TODO: different colours
        colors = {
            highlight_category: _default_colour
            for highlight_category in highlight_categories
        }

    n_rdms_x, n_rdms_y = len(rdms_x), len(rdms_y)

    gridspec = _set_up_gridspec(n_rdms_x, n_rdms_y, show_marginal_distributions)

    fig: Figure = pyplot.figure(figsize=(8, 8))

    # To share x and y axes when using gridspec you need to specify which axis to use as references.
    # The reference axes will be those in the first column and those in the last row.
    reference_axis = None
    # Remember axes for scatter plots now so we can draw to them all later
    scatter_axes: List[Axes] = []
    for scatter_col_idx, rdm_for_col in enumerate(rdms_x):
        is_leftmost_col = (scatter_col_idx == 0)
        if show_marginal_distributions:
            # distributions show in the first column, so need to bump the column index
            scatter_col_idx += 1
        # Since matplotlib ordering is left-to-right, top-to-bottom, we need to process the rows in reverse to get the
        # correct reference axis.
        for scatter_row_idx in reversed(range(n_rdms_y)):
            is_bottom_row = (scatter_row_idx == n_rdms_y - 1)

            # RDMs objects aren't iterators, so while we can do `for r in rdms`, we can't do `reversed(rdms)`.
            # Hence we have to pull the rdm out by its index.
            rdm_for_row = rdms_y[scatter_row_idx]

            if reference_axis is None:
                sub_axis: Axes = fig.add_subplot(gridspec[scatter_row_idx, scatter_col_idx])
                reference_axis = sub_axis
            else:
                sub_axis: Axes = fig.add_subplot(gridspec[scatter_row_idx, scatter_col_idx],
                                                 sharex=reference_axis, sharey=reference_axis)

            # First plot dissimilarities within all stimuli
            full_marker_size = rcParams["lines.markersize"] ** 2
            sub_axis.scatter(x=rdm_for_col.get_vectors(),
                             y=rdm_for_row.get_vectors(),
                             color=_default_colour,
                             s=full_marker_size,
                             cmap=cmap)

            if highlight_category_selector is not None:

                within_category_idxs = _get_within_category_idxs(highlight_categories=highlight_categories,
                                                                 category_idxs=category_idxs,
                                                                 n_cond=rdms_x.n_cond)

                between_category_idxs = _get_between_category_idxs(category_idxs=category_idxs,
                                                                   highlight_categories=highlight_categories,
                                                                   n_cond=rdms_x.n_cond)

                within_category_dissims, between_category_dissims = _split_dissimilarities_within_between(
                    dissimilarities_for_row=rdm_for_row.get_vectors(),
                    dissimilarities_for_col=rdm_for_col.get_vectors(),
                    within_category_idxs=within_category_idxs,
                    between_category_idxs=between_category_idxs,
                )

                # Plot between highlighted categories
                colours_between = _colours_between_categories(highlight_categories, colors)
                for categories in between_category_idxs.keys():
                    sub_axis.scatter(x=between_category_dissims[categories][0],
                                     y=between_category_dissims[categories][1],
                                     color=colours_between[categories],
                                     # Slightly smaller, so the points for all still shows
                                     s=full_marker_size * 0.5,
                                     cmap=cmap)

                # Plot within highlighted categories
                for category_name in within_category_idxs.keys():
                    sub_axis.scatter(x=within_category_dissims[category_name][0],
                                     y=within_category_dissims[category_name][1],
                                     color=colors[category_name],
                                     # Slightly smaller still, so the points for all and between still show
                                     s=full_marker_size * 0.3,
                                     cmap=cmap)

            scatter_axes.append(sub_axis)

            _do_format_sub_axes(sub_axis, is_bottom_row, is_leftmost_col)

    if show_marginal_distributions:
        _do_show_marginal_distributions(fig, reference_axis, gridspec, rdms_x, rdms_y, hist_bins,
                                        highlight_categories, category_idxs, colors)

    if show_identity_line:
        _do_show_identity_line(reference_axis, scatter_axes)

    if axlim is not None:
        _do_set_axes_limits(axlim, reference_axis)

    return fig


def _handle_args_highlight_categories(highlight_category_selector, highlight_categories, reference_rdms) -> Optional[Dict[str, List[int]]]:
    # Handle category highlighting args
    _msg_arg_highlight = "Arguments `highlight_category_selector` and `highlight_categories` must be compatible."
    try:
        if highlight_category_selector is None:
            assert highlight_categories is None
            # If we get here we'll never use this value, but we need to satisfy the static analyser that it's
            # initialised under all code paths..
            category_idxs = None
        else:
            assert highlight_categories is not None
            category_idxs = category_condition_idxs(reference_rdms, highlight_category_selector)
            assert all(c in category_idxs.keys() for c in highlight_categories)
    except AssertionError as exc:
        raise ValueError(_msg_arg_highlight) from exc
    return category_idxs


def _handle_args_rdms(rdms):
    _msg_arg_rdms = "Argument `rdms` must be an RDMs or pair of RDMs objects."

    rdms_x: RDMs  # RDM for the x-axis, or RDMs for facet columns
    rdms_y: RDMs  # RDM for the y-axis, or RDMs for facet rows
    try:
        if isinstance(rdms, RDMs):
            # 1 supplied
            rdms_x, rdms_y = rdms, rdms
        else:
            # Check that only 2 supplied
            assert len(rdms) == 2
            rdms_x, rdms_y = rdms[0], rdms[1]
        assert len(rdms_x) > 0
        assert len(rdms_y) > 0
    except TypeError:
        raise ValueError(_msg_arg_rdms)
    except AssertionError as exc:
        raise ValueError(_msg_arg_rdms) from exc
    return rdms_x, rdms_y


def _do_format_sub_axes(sub_axis, is_bottom_row: bool, is_leftmost_col: bool):
    # Square axes
    # sub_axis.set_aspect('equal', adjustable='box')

    # Hide the right and top spines
    sub_axis.spines['right'].set_visible(False)
    sub_axis.spines['top'].set_visible(False)

    # Hide all but the outermost ticklabels
    if not is_bottom_row:
        pyplot.setp(sub_axis.get_xticklabels(), visible=False)
    if not is_leftmost_col:
        pyplot.setp(sub_axis.get_yticklabels(), visible=False)


def _do_set_axes_limits(axlim, reference_axis):
    reference_axis.set_xlim(axlim[0], axlim[1])
    reference_axis.set_ylim(axlim[0], axlim[1])


def _set_up_gridspec(n_rdms_x, n_rdms_y, show_marginal_distributions):
    grid_n_rows = n_rdms_y
    grid_n_cols = n_rdms_x
    grid_width_ratios = tuple(6 for _ in range(grid_n_cols))
    grid_height_ratios = tuple(6 for _ in range(grid_n_rows))
    if show_marginal_distributions:
        # Add extra row & col for marginal distributions
        grid_n_rows += 1
        grid_n_cols += 1
        grid_width_ratios = (1, *grid_width_ratios)
        grid_height_ratios = (*grid_height_ratios, 1)
    gridspec = GridSpec(
        nrows=grid_n_rows,
        ncols=grid_n_cols,
        width_ratios=grid_width_ratios,
        height_ratios=grid_height_ratios,
    )
    return gridspec


def _do_show_identity_line(reference_axis, scatter_axes):
    for ax in scatter_axes:
        # Prevent autoscale, else plotting from the origin causes the axes to rescale
        ax.autoscale(False)
        ax.plot([reference_axis.get_xlim()[0], reference_axis.get_xlim()[1]],
                [reference_axis.get_ylim()[0], reference_axis.get_ylim()[1]],
                # Grey line in the background
                "0.5", zorder=-1)


def _do_show_marginal_distributions(fig, reference_axis, gridspec, rdms_x, rdms_y, hist_bins,
                                    highlight_categories, category_idxs, colors):

    # Add marginal distributions along the x axis
    reference_hist = None
    for col_idx, rdm_for_col in enumerate(rdms_x):
        if reference_hist is None:
            hist_axis: Axes = fig.add_subplot(gridspec[-1, col_idx + 1], sharex=reference_axis)
            reference_hist = hist_axis
        else:
            hist_axis: Axes = fig.add_subplot(gridspec[-1, col_idx + 1], sharex=reference_axis, sharey=reference_hist)

        # Plot all dissims
        hist_axis.hist(rdm_for_col.get_vectors().flatten(), histtype='step', fill=False,
                       orientation='vertical', bins=hist_bins, color=_default_colour)

        if highlight_categories is not None:
            # Plot within dissims
            within_category_idxs = _get_within_category_idxs(highlight_categories, category_idxs, rdm_for_col.n_cond)
            for category_name, idxs in within_category_idxs.items():
                hist_axis.hist(rdm_for_col.dissimilarities[idxs], histtype='step', fill=False,
                               orientation='vertical', bins=hist_bins, color=colors[category_name])

            # Plot between dissims
            between_category_idxs = _get_between_category_idxs(category_idxs, highlight_categories, rdm_for_col.n_cond)
            colours_between = _colours_between_categories(highlight_categories, colors)
            for categories, idxs in between_category_idxs.items():
                hist_axis.hist(rdm_for_col.dissimilarities[idxs], histtype='step', fill=False,
                               orientation='vertical', bins=hist_bins, color=colours_between[categories])

        hist_axis.xaxis.set_visible(False)
        hist_axis.yaxis.set_visible(False)
        hist_axis.set_frame_on(False)
    # Flip to pointing downwards
    reference_hist.set_ylim(hist_axis.get_ylim()[::-1])

    # Add marginal distributions along the y axis
    reference_hist = None
    for row_idx, rdm_for_row in enumerate(rdms_y):
        if reference_hist is None:
            hist_axis: Axes = fig.add_subplot(gridspec[row_idx, 0], sharey=reference_axis)
            reference_hist = hist_axis
        else:
            hist_axis: Axes = fig.add_subplot(gridspec[row_idx, 0], sharey=reference_axis, sharex=reference_hist)

        # Plot all dissims
        hist_axis.hist(rdm_for_row.get_vectors().flatten(), histtype='step', fill=False, orientation='horizontal',
                       bins=hist_bins)

        if highlight_categories is not None:
            # Plot within dissims
            within_category_idxs = _get_within_category_idxs(highlight_categories, category_idxs, rdm_for_row.n_cond)
            for category_name, idxs in within_category_idxs.items():
                hist_axis.hist(rdm_for_row.dissimilarities[idxs], histtype='step', fill=False,
                               orientation='horizontal', bins=hist_bins, color=colors[category_name])

            # Plot between dissims
            between_category_idxs = _get_between_category_idxs(category_idxs, highlight_categories, rdm_for_row.n_cond)
            colours_between = _colours_between_categories(highlight_categories, colors)
            for categories, idxs in between_category_idxs.items():
                hist_axis.hist(rdm_for_row.dissimilarities[idxs], histtype='step', fill=False,
                               orientation='horizontal', bins=hist_bins, color=colours_between[categories])

        hist_axis.xaxis.set_visible(False)
        hist_axis.yaxis.set_visible(False)
        hist_axis.set_frame_on(False)
    # Flip to pointing leftwards
    reference_hist.set_xlim(hist_axis.get_xlim()[::-1])


def _get_within_category_idxs(
        highlight_categories: List[str],
        category_idxs: Dict[str, List[int]],
        n_cond: int) -> Dict[str, List[int]]:

    # category name -> [idxs]
    within_category_idxs: Dict[str, List[int]] = dict()

    for category_name in highlight_categories:
        # Get UTV binary mask for within-category dissims
        square_mask = square_category_binary_mask(category_idxs=category_idxs[category_name], size=n_cond)
        # We don't use diagonal entries, but they must be 0 for squareform to work
        fill_diagonal(square_mask, False)  # in place
        within_category_idxs[category_name] = squareform(square_mask)[np.newaxis]

    return within_category_idxs


def _get_between_category_idxs(category_idxs, highlight_categories, n_cond) -> Dict[frozenset, List[int]]:
    # {category1, category2} -> [idxs]
    between_category_idxs: Dict[frozenset, List[int]] = dict()
    exhausted_categories = []
    for category_1_name in highlight_categories:
        for category_2_name in highlight_categories:
            # Don't do between a category and itself
            if category_1_name == category_2_name:
                continue
            # Don't double-count between-category dissims; just restrict to UTV
            if category_2_name in exhausted_categories:
                continue

            between_category_idxs[frozenset({category_1_name, category_2_name})] = squareform(
                square_between_category_binary_mask(category_1_idxs=category_idxs[category_1_name],
                                                    category_2_idxs=category_idxs[category_2_name],
                                                    size=n_cond))[np.newaxis]
        exhausted_categories.append(category_1_name)
    return between_category_idxs


def _split_dissimilarities_within_between(
        dissimilarities_for_row: array,
        dissimilarities_for_col: array,
        within_category_idxs,
        between_category_idxs):
    """
    Splits dissimilarities into within/between category dissimilarities for highlighted categories.
    """

    # Within categories
    # category name -> (xs, ys)
    within_category_dissims: Dict[str, Tuple[List[float], List[float]]] = {
        category_name: (
            dissimilarities_for_col[idxs],  # x
            dissimilarities_for_row[idxs],  # y
        )
        for category_name, idxs in within_category_idxs.items()
    }

    # Between categories
    # {category1, category2} -> (xs, ys)
    between_category_dissims: Dict[frozenset, Tuple[List[float], List[float]]] = {
        categories: (
                dissimilarities_for_col[idxs],  # x
                dissimilarities_for_row[idxs],  # y
        )
        for categories, idxs in between_category_idxs.items()
    }
    return within_category_dissims, between_category_dissims


def _colours_between_categories(highlight_categories, colours):

    # {category1, category2} -> colour
    between_category_colours: Dict[frozenset, _Colour] = dict()

    exhausted_categories = []
    for category_1_name in highlight_categories:
        for category_2_name in highlight_categories:
            between_category_colours[frozenset({category_1_name, category_2_name})] = _blend_rgb_colours(
                colours[category_1_name],
                colours[category_2_name]
            )
        exhausted_categories.append(category_1_name)

    return between_category_colours


def _blend_rgb_colours(c1, c2=None):
    if c2 is None:
        return c1
    else:
        return (
            (c1[0]+c2[0])/2,  # R
            (c1[1]+c2[1])/2,  # G
            (c1[2]+c2[2])/2,  # B
        )
