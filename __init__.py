import yapapi
import os, sys # debug sys
from yapapi import rest
from typing import Optional
from yapapi.strategy import SCORE_REJECTED, SCORE_NEUTRAL, SCORE_TRUSTED, MarketStrategy, DecreaseScoreForUnconfirmedAgreement, LeastExpensiveLinearPayuMS
from yapapi.props import com
from decimal import Decimal
import json

# originally a method from yapapi.golem::Golem (yapapi 0.9)
def _initialize_default_strategy() -> DecreaseScoreForUnconfirmedAgreement:

    """Create a default strategy and register it's event consumer"""
    base_strategy = LeastExpensiveLinearPayuMS(
            max_fixed_price=Decimal("1.0"),
            max_price_for={com.Counter.CPU: Decimal("0.2"), com.Counter.TIME: Decimal("0.1")},
            )
    strategy = DecreaseScoreForUnconfirmedAgreement(base_strategy, 0.5)
    # self._event_consumers.append(strategy.on_event)
    return strategy

def _convert_string_array_to_list(stringarray):
    """inputs 1) a stringarray bounded by [ ] with unquoted list elements and converts to a list of strings
    or 2) an unbounded string that is a single word which is placed as a string in a list
    then returns the list or an empty list
    """
    error = False
    done = False
    thelist=[]

    if not isinstance(stringarray, str):
        error=True


    if not error and not done:
        if len(stringarray) == 0:
            error=True

    if not error and not done:
        if stringarray[0]!='[':
            thelist.append(stringarray)
            done = True

    if not error and not done:
        if len(stringarray) < 3:
            error=True # a input bracketed string must have at least one element (character) to listify

    if not error and not done: # not done implies begins with '['
        if (stringarray[-1]==']'):
            thelist.append(stringarray)
        else:
            error=True

    if not error and not done:
        thelist=stringarray[1:-1].split(',')


    return thelist if not error else []




def _partial_match_in(cf, node_addresses):
    for node_address in node_addresses:
        if cf.startswith(node_address):
            return True
    return False



class FilterProviderMS(MarketStrategy):
    def __init__(self, wrapped=None, ansi=True):
        # make sure wrapped is a descendant of marketstrategy TODO
        self._default=_initialize_default_strategy()
        self._wrapped=wrapped if wrapped != None else self._default
        self._seen_rejected = set()
        self._motd = False
        self._VERBOSE=os.environ.get('FILTERMSVERBOSE')

        if not self._motd:
            if not self._VERBOSE:
                print(f"[filterms] TO SEE ALL REJECTIONS SET THE ENVIRONMENT VARIABLE FILTERMSVERBOSE TO 1", file=sys.stderr)
            self._motd=True

    async def score_offer(self, offer) -> float:
        seen_rejected=self._seen_rejected
        VERBOSE=self._VERBOSE
        blacklisted=False
        provider_names = []
        provider_names_bl = []
        score = None
        name = offer.props["golem.node.id.name"]


        try: 
            provider_names=_convert_string_array_to_list( os.environ.get('GNPROVIDER') )
            provider_names_bl=_convert_string_array_to_list( os.environ.get('GNPROVIDER_BL') )

            # GNPROVIDER may be a bracketed expression implying a json array, otherwise a single value FUTURE IMPLEMENTATION
            if len(provider_names_bl) > 0: # blacklisting
                if name in provider_names_bl: # match name
                    blacklisted=True
                    if name not in seen_rejected: # prince once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: blacklisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)
                elif _partial_match_in(offer.issuer, provider_names_bl): # partial match node address
                    blacklisted=True
                    if name not in seen_rejected: # print once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: blacklisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)
                if blacklisted:
                    score = SCORE_REJECTED

            if not blacklisted and len(provider_names) > 0: # whitelisting
                if name in provider_names: # match name
                    score = await self._wrapped.score_offer(offer)
                elif _partial_match_in(offer.issuer, provider_names): # partial match node address
                    score = await self._wrapped.score_offer(offer)
                else:
                    score = SCORE_REJECTED

                if score != SCORE_REJECTED and score != None:
                    print(f'[filterms] ACCEPTED offer from {name} scored at: {score}', file=sys.stderr, flush=True)
                    if VERBOSE:
                        print(f'\n{offer.props}\n')
                else:
                    if VERBOSE and name not in seen_rejected: # print once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: not whitelisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)

            if score==None:
                score=await self._wrapped.score_offer(offer)

        except Exception as e:
            print("[filterms] AN UNHANDLED EXCEPTION OCCURRED", file=sys.stderr)
            print(e, file=sys.stderr)

        return score

    async def decorate_demand(self, demand):
        return await self._wrapped.decorate_demand(demand)



