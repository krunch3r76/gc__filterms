import yapapi
import os, sys # debug sys
from yapapi import rest
from typing import Optional
from yapapi.strategy import SCORE_REJECTED, SCORE_NEUTRAL, SCORE_TRUSTED, ComputationHistory
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


class FilterProviderMS(yapapi.strategy.LeastExpensiveLinearPayuMS):
    async def score_offer(
            self, offer: rest.market.OfferProposal, history: Optional[ComputationHistory] = None
            ) -> float:
        blacklisted=False
        provider_names = []
        provider_names_bl = []
        score = SCORE_REJECTED
        try: 
            provider_names=_convert_string_array_to_list( os.environ.get('GNPROVIDER') )
            provider_names_bl=_convert_string_array_to_list( os.environ.get('GNPROVIDER_BL') )
            # print(f"provider_names_bl: {provider_names_bl}") 
            # GNPROVIDER may be a bracketed expression implying a json array, otherwise a single value

            if len(provider_names_bl) > 0 and len(provider_names) > 0:
                print(f"[filterProviderMS] ERROR, can have either a whitelist or blacklist but not both! Ignoring")
                score=await super().score_offer(offer, history)
            elif len(provider_names_bl) > 0:
                if offer.props["golem.node.id.name"] in provider_names_bl:
                    blacklisted=True
                    print(f'REJECTED offer from {offer.props["golem.node.id.name"]}, reason: blacklisted!', flush=True)
            elif len(provider_names) > 0:
                if offer.props["golem.node.id.name"] in provider_names:
                    score = await super().score_offer(offer, history)

                if len(provider_names) > 0:
                    if score != SCORE_REJECTED:
                        print(f'ACCEPTED offer from {offer.props["golem.node.id.name"]}', flush=True)
                        print(f'\n{offer.props}\n')
                    else:
                        print(f'REJECTED offer from {offer.props["golem.node.id.name"]}', flush=True)
            else:
                return await super().score_offer(offer, history)

        except Exception as e:
            print("AN UNHANDLED EXCEPTION OCCURRED")
            print(e)

        return score

filterProviderMS = FilterProviderMS()
