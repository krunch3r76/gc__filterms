import yapapi
import os
from yapapi import rest
from typing import Optional
from yapapi.strategy import SCORE_REJECTED, SCORE_NEUTRAL, SCORE_TRUSTED, ComputationHistory







class FilterProviderMS(yapapi.strategy.LeastExpensiveLinearPayuMS, object):

    async def score_offer(
            self, offer: rest.market.OfferProposal, history: Optional[ComputationHistory] = None
            ) -> float:


        provider_names = []
        score = SCORE_REJECTED
        
        provider = os.environ.get('PROVIDER')

        if provider:
            provider_names.append(provider)

        if len(provider_names) > 0:
            if offer.props["golem.node.id.name"] in provider_names:
                score = await super().score_offer(offer, history)
        else:
            score = await super().score_offer(offer, history)

        if score != SCORE_REJECTED:
            print(f'ACCEPTED offer from {offer.props["golem.node.id.name"]}', flush=True)
            print(f'{offer.props}')
        else:
            print(f'REJECTED offer from {offer.props["golem.node.id.name"]}', flush=True)

        return score

filterProviderMS = FilterProviderMS()
