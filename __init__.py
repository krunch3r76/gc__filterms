import yapapi
import os, sys # debug sys
from yapapi import rest
from typing import Optional
from yapapi.strategy import SCORE_REJECTED, SCORE_NEUTRAL, SCORE_TRUSTED, ComputationHistory, MarketStrategy
import json


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
        self._default=yapapi.strategy.LeastExpensiveLinearPayuMS()
        self._wrapped=wrapped if wrapped else self._default
        self._seen_rejected = set()
        self._motd = False
        self._VERBOSE=os.environ.get('FILTERMSVERBOSE')

        if not self._motd:
            if not self._VERBOSE:
                print(f"[filterms] TO SEE ALL REJECTIONS SET THE ENVIRONMENT VARIABLE FILTERMSVERBOSE TO 1", file=sys.stderr)
            self._motd=True

    async def score_offer(
            self, offer: rest.market.OfferProposal, history: Optional[ComputationHistory] = None
            ) -> float:
        seen_rejected=self._seen_rejected
        VERBOSE=self._VERBOSE
        blacklisted=False
        provider_names = []
        provider_names_bl = []
        score = SCORE_REJECTED
        name = offer.props["golem.node.id.name"]


        try: 
            provider_names=_convert_string_array_to_list( os.environ.get('GNPROVIDER') )
            provider_names_bl=_convert_string_array_to_list( os.environ.get('GNPROVIDER_BL') )

            # GNPROVIDER may be a bracketed expression implying a json array, otherwise a single value FUTURE IMPLEMENTATION
            if len(provider_names_bl) > 0 and len(provider_names) > 0:
                print(f"[filterms] ERROR, can have either a whitelist or blacklist but not both! Ignoring", file=sys.stderr)
                score=await self._wrapped.score_offer(offer, history)
            elif len(provider_names_bl) > 0: # blacklisting
                if name in provider_names_bl: # match name
                    blacklisted=True
                    if VERBOSE and name not in seen_rejected: # prince once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: blacklisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)
                elif _partial_match_in(offer.issuer, provider_names_bl): # partial match node address
                    blacklisted=True
                    if VERBOSE and name not in seen_rejected: # print once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: blacklisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)
                if not blacklisted:
                    score = await self._wrapped.score_offer(offer, history)
            elif len(provider_names) > 0: # whitelisting
                if name in provider_names: # match name
                    score = await self._wrapped.score_offer(offer, history)
                elif _partial_match_in(offer.issuer, provider_names): # partial match node address
                    score = await self._wrapped.score_offer(offer, history)
                if score != SCORE_REJECTED:
                    print(f'[filterms] ACCEPTED offer from {name}', file=sys.stderr, flush=True)
                    if VERBOSE:
                        print(f'\n{offer.props}\n')
                else:
                    if VERBOSE and name not in seen_rejected: # print once when verbose
                        print(f'[filterms] \033[5mREJECTED\033[0m offer from {name}, reason: not whitelisted!', file=sys.stderr, flush=True)
                    seen_rejected.add(name)
            else: # neither environment var set, just fallback to call wrapped score_offer
                score=await self._wrapped.score_offer(offer, history)

        except Exception as e:
            print("[filterms] AN UNHANDLED EXCEPTION OCCURRED", file=sys.stderr)
            print(e, file=sys.stderr)

        return score

    async def decorate_demand(self, demand):
        return await self._wrapped.decorate_demand(demand)



