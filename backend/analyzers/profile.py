from ..schemas import Profile, AnalyzeRequest
from pydantic import BaseModel
from typing import Optional

class ProfileComparison(BaseModel):
    known_device: Optional[bool]
    location_matches: Optional[bool]
    hour_typical: Optional[bool]
    amount_ratio: Optional[float]
    new_recipient: Optional[bool]
    usual_amount_inr: Optional[float]

def compare_to_profile(profile: Profile, request: AnalyzeRequest) -> ProfileComparison:
    baseline = profile.baseline
    
    known_device = None
    if baseline.usual_devices and request.context.device_label:
        known_device = (request.context.device_label in baseline.usual_devices)

    location_matches = None
    if baseline.usual_locations and request.context.location_label:
        location_matches = (request.context.location_label in baseline.usual_locations)

    hour_typical = None
    if baseline.normal_hours:
        hour = request.context.local_hour
        if baseline.normal_hours.start <= baseline.normal_hours.end:
            hour_typical = (baseline.normal_hours.start <= hour <= baseline.normal_hours.end)
        else:
            hour_typical = (hour >= baseline.normal_hours.start or hour <= baseline.normal_hours.end)

    usual_amount = None
    amount_ratio = None
    new_recipient = None

    if baseline.transaction_patterns:
        # Check if recipient is known in any pattern
        recip = request.transaction.recipient_label
        if recip:
            known = any(recip in p.typical_payees for p in baseline.transaction_patterns)
            new_recipient = not known
            
        # For usual_amount, take the maximum max_amount among patterns
        max_amt = max(p.max_amount for p in baseline.transaction_patterns)
        if max_amt > 0:
            usual_amount = max_amt
            if request.transaction.amount_inr is not None:
                amount_ratio = request.transaction.amount_inr / usual_amount

    return ProfileComparison(
        known_device=known_device,
        location_matches=location_matches,
        hour_typical=hour_typical,
        amount_ratio=amount_ratio,
        new_recipient=new_recipient,
        usual_amount_inr=usual_amount
    )
