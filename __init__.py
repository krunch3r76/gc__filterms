# filterms.py
# authored by krunch3r76 (https://www.github.com/krunch3r76)
# license GPL 3.0

import yapapi
import os, sys  # debug sys
from yapapi import rest
from typing import Optional
from yapapi.strategy import (
    SCORE_REJECTED,
    SCORE_NEUTRAL,
    SCORE_TRUSTED,
    MarketStrategy,
    DecreaseScoreForUnconfirmedAgreement,
    LeastExpensiveLinearPayuMS,
    WrappingMarketStrategy,
)
from yapapi.props import com
from decimal import Decimal
import json
from .provider_filter import ProviderFilter
import inspect

import logging
from collections.abc import Iterable


def _print_err(*args, **kwargs):

    """wrapper around print to route to stderr"""
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


# originally a method from yapapi.golem::Golem (yapapi 0.9)
# creates sane defaults for a marketstrategy
def _initialize_default_strategy() -> DecreaseScoreForUnconfirmedAgreement:

    """Create a default strategy and register it's event consumer"""
    base_strategy = LeastExpensiveLinearPayuMS(
        max_fixed_price=Decimal("1.0"),
        max_price_for={
            com.Counter.CPU: Decimal("0.2"),
            com.Counter.TIME: Decimal("0.1"),
        },
    )
    strategy = DecreaseScoreForUnconfirmedAgreement(base_strategy, 0.5)
    # self._event_consumers.append(strategy.on_event)
    return strategy


class _ProviderInfo:

    """store name@provider_id as hashable along with other relevant offer info"""

    def __init__(self, name, provider_id, cpu_capabilities):
        self.__name = name
        self.__provider_id = provider_id
        self.__cpu_capabilities = cpu_capabilities

    @property
    def name(self):
        return self.__name

    @property
    def provider_id(self):
        return self.__provider_id

    @property
    def cpu_capabilities(self):
        return self.__cpu_capabilities

    def check_cpu_capabilities(self, features):
        """ensure all capabilities are present on the offer"""
        assert isinstance(features, Iterable)
        if len(features) == 0:
            return True
        return all(map(lambda feature: feature in self.cpu_capabilities, features))

    def __repr__(self):
        return f"{self.name}@{self.provider_id}"

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def fuzzy_matches(self, name_or_partial_id):
        """determine if either name or partial address corresponds to internals"""
        whether_name_matches = False
        whether_partial_id_matches = False

        if name_or_partial_id == self.name:
            whether_name_matches = True
        if self.provider_id.startswith(name_or_partial_id):
            whether_partial_id_matches = True

        return whether_name_matches ^ whether_partial_id_matches


class FilterProviderMS(ProviderFilter):
    """
    :_VERBOSE               verbose logging (determined by presence of env:FILTERMSVERBOSE
    :_previously_rejected   a set of previously rejected providers
    :_seen_providers        a set of all unique providers seen thus far

    """

    #               __init__                                                 <
    def __init__(self, base_strategy=None, features=None):

        # -          _convert_string_array_to_list                          -<
        def _convert_string_array_to_list(stringarray):

            """take a string that represents a single value or a bracketed array
            and return enclosed in a python list

            inputs 1) a stringarray bounded by [ ] with unquoted list elements and
            converts to a list of strings
            or 2) an unbounded string that is a single word which is placed as a string in a list
            then returns the list or an empty list
            """

            error = False
            done = False
            thelist = []

            if stringarray == None:
                error = True

            if not error and not isinstance(stringarray, str):
                error = True

            if not error and not done:
                if len(stringarray) == 0:
                    error = True

            if not error and not done:
                if stringarray[0] != "[":
                    thelist.append(stringarray)
                    done = True

            if not error and not done:
                if len(stringarray) < 3:
                    error = True  # a input bracketed string must have at least one element (character) to listify

            if not error and not done:  # not done implies begins with '['
                if stringarray[-1] == "]":
                    thelist.append(stringarray)
                else:
                    error = True

            if not error and not done:
                thelist = stringarray[1:-1].split(",")

            return thelist if not error else []

        # /-          _convert_string_array_to_list                          ->

        def setup_logger(self):
            self._logger = logging.getLogger("filterms")
            stream_handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter("[filterms] %(levelname)s - %(message)s")
            stream_handler.setFormatter(formatter)
            self._logger.addHandler(stream_handler)
            self._logger.setLevel(logging.INFO)
            if self._VERBOSE:
                self._logger.setLevel(logging.DEBUG)
            if not self._VERBOSE:
                self._logger.info(
                    f"TO SEE ALL REJECTIONS SET THE ENVIRONMENT VARIABLE FILTERMSVERBOSE TO 1",
                )

        self._VERBOSE = os.environ.get("FILTERMSVERBOSE")

        self._provider_fuzzy_bl = _convert_string_array_to_list(
            os.environ.get("GNPROVIDER_BL")
        )

        self._provider_fuzzy_wl = _convert_string_array_to_list(
            os.environ.get("GNPROVIDER")
        )
        setup_logger(self)
        self._logger.debug(f"fuzzy whitelist is {self._provider_fuzzy_wl}")
        if features == None:
            features = _convert_string_array_to_list(os.environ.get("GNFEATURES"))
        elif isinstance(features, str):
            features = [features]
        elif not isinstance(features, Iterable):
            self._logger.warning(
                "Features argument is neither a string nor an iterable: IGNORED!"
            )
            features = list()
        self._features = features

        if base_strategy == None:
            base_strategy = _initialize_default_strategy()
        super().__init__(base_strategy, is_allowed=self._is_allowed)

        self._previously_rejected = set()
        self._seen_providers = set()

        # print(
        #     f"[filterms] TO SEE ALL REJECTIONS SET THE ENVIRONMENT VARIABLE FILTERMSVERBOSE TO 1",
        #     file=sys.stderr,
        # )

        self._providerInfo_bl = set()
        self._providerInfo_wl = set()
        self._providersSeenSoFar = set()
        self._providersBlacklistedSoFar = set()

        self._logger.debug(f"filtering providers with cpu features in {self._features}")

    async def _is_allowed(self, provider_id):
        try:

            def _lookup_provider_by_id(self, provider_id):
                """find matching providerInfo"""
                matched = list(
                    filter(
                        lambda providerInfo: provider_id == providerInfo.provider_id,
                        self._providersSeenSoFar,
                    )
                )
                if len(matched) < 1:  # should be 1...
                    emsg = "fatal error! provider_id not stored internally!"
                    self._logger.critical(emsg)
                    # raise Exception(emsg)
                return matched[0]

            matched_on_blacklist = False
            matched_on_whitelist = True
            matched_on_features = False
            # matched_on_secondary_criteria = True # TODO
            allowed = False

            providerInfo = _lookup_provider_by_id(self, provider_id)

            # if providerInfo in self._providersBlacklistedSoFar:
            #     self._logger.debug("UNEXPECTED REPEAT OFFER!")
            #     return False

            # check blacklist
            matching_bl = list(
                filter(
                    lambda providerInfo: provider_id == providerInfo.provider_id,
                    self._providerInfo_bl,
                )
            )
            matched_on_blacklist = len(matching_bl) == 1

            if matched_on_blacklist:
                self._logger.debug(
                    f"{providerInfo} rejected due to blacklist membership"
                )
            elif len(self._provider_fuzzy_wl) > 0:  # whitelisting activated
                if len(self._providerInfo_wl) > 0:
                    # check whitelist
                    matched_on_whitelist = False  # ensure not on list rejected
                    matching_wl = list(
                        filter(
                            lambda providerInfo: provider_id
                            == providerInfo.provider_id,
                            self._providerInfo_wl,
                        )
                    )
                    matched_on_whitelist = len(matching_wl) > 0
                else:
                    matched_on_whitelist = (
                        False  # whitelisting requested but not a match
                    )
                    self._logger.debug(f"rejected {providerInfo}, not on whitelist")

            matched_on_features = providerInfo.check_cpu_capabilities(self._features)

            if not matched_on_features:
                self._logger.debug(
                    f"{providerInfo} rejected due to missing cpu feature(s)"
                )
                # self._logger.debug(
                #     f"the following provider did not have the required feature(s):"
                #     f" {providerInfo}"
                #     f"\n{providerInfo.cpu_capabilities}"
                # )

        except Exception as e:
            self._logger.critical(f"_is_allowed threw an unhandled exception: {e}")
            raise e

        allowed = (
            (not matched_on_blacklist)
            and matched_on_whitelist
            and matched_on_features
            # and matched_on_secondary_criteria
        )

        if not allowed:
            self._providersBlacklistedSoFar.add(providerId)

        return allowed

    # /              __init__                                                 >

    async def score_offer(self, offer) -> float:
        def _extract_provider_info_from_offer(offer):
            return offer.props["golem.node.id.name"], offer.issuer

        try:

            providerInfo = _ProviderInfo(
                *_extract_provider_info_from_offer(offer),
                offer.props.get(
                    "golem.inf.cpu.capabilities", []
                ),  # kludge to handle missing field
            )

            name = _extract_provider_info_from_offer(offer)

            self._providersSeenSoFar.add(providerInfo)
            if any(
                map(
                    lambda candidate: providerInfo.fuzzy_matches(candidate),
                    self._provider_fuzzy_bl,
                )
            ):
                # add to internal set of blacklisted providers
                self._providerInfo_bl.add(providerInfo)
            elif any(
                map(
                    lambda candidate: providerInfo.fuzzy_matches(candidate),
                    self._provider_fuzzy_wl,
                )
            ):
                self._providerInfo_wl.add(providerInfo)

        except Exception as e:
            self._logger.critical(f"an unhandled exception: {e}, occurred")

        return await super().score_offer(offer)
