from enum import Enum


class ErrorCodes(Enum):
    """ """
    #
    # NOTE: Testing to see if Enums as error codes is usable.
    #

    e0100 = 'Settings Error: ({0!s}).'
    e0110 = 'Settings Error: ({0!s}) is an invalid value. API Request Timeout must be a integer.'
    e0120 = 'Settings Error: ({0!s}) is an invalid value. API Retries must be a integer.'
    e0130 = 'Settings Error: ({0!s}) is an invalid value. API Sleep must be a integer.'
    e0140 = 'Settings Error: ({0!s}) is an invalid value. Max result counts must be a integer.'
    e0150 = 'Settings Error: Type {0!s} must be a IndicatorType.'
    e0160 = 'Settings Error: ({0!s}) is an invalid compiled regex.'

    #
    # Resource Error Codes
    #
    e0500 = 'Resource Error: ({0!s}) is an invalid resource type. Resource types must be a ResourceKey enum.'

    #
    # Filter Error Codes
    #
    e1000 = 'Filter Error: ({0!s}) is an invalid filter operator. Filter Operators must be a FilterSetOperator Enum.'
    e1010 = 'Filter Error: ({0!s}) is an invalid filter operator. Filter Operators must be a FilterOperator Enum.'

    # group filters
    e4000 = 'Filter Error: ({0!s}) is an invalid adversary ID. The adversary ID must be an integer.'
    e4005 = 'Filter Error: ({0!s}) is an invalid campaign ID. The campaign ID must be an integer.'
    e4010 = 'Filter Error: ({0!s}) is an invalid document ID. The document ID must be an integer.'
    e4020 = 'Filter Error: ({0!s}) is an invalid email ID. The email ID must be an integer.'
    e4030 = 'Filter Error: ({0!s}) is an invalid ID. The ID must be an integer.'
    e4040 = 'Filter Error: ({0!s}) is an invalid incident ID. The incident ID must be an integer.'
    e4050 = 'Filter Error: ({0!s}) is an invalid Security Label. The Security Label must be a string.'
    e4060 = 'Filter Error: ({0!s}) is an invalid signature ID. The signature ID must be an integer.'
    e4070 = 'Filter Error: ({0!s}) is an invalid Tag. The Tag must be a string.'
    e4080 = 'Filter Error: ({0!s}) is an invalid threat ID. The threat ID must be an integer.'
    e4090 = 'Filter Error: ({0!s}) is an invalid victim ID. The victim ID must be an integer.'

    # indicator filters
    e5000 = 'Filter Error: ({0!s}) is an invalid Group ID. The Group ID must be an integer.'
    e5001 = 'Filter Error: ({0!s}) is an invalid Group Type. The Group Type must be a GroupType Enum.'
    e5010 = 'Filter Error: ({0!s}) is an invalid indicator.'
    e5011 = 'Filter Error: ({0!s}) is an invalid indicator type. The Indicator Type must be an GroupType Enum.'
    e5020 = 'Filter Error: ({0!s}) is an invalid Victim ID. The Victim ID must be an integer.'
    e5100 = 'Filter Error: Only one type can be added to a filter. The current filter type is ({0!s}).'

    # Request Object
    e6000 = 'Request Object Error: {0!s} is not a valid HTTP method.'

    #
    # Resource Object Error Codes
    #
    e10000 = 'Resource Error: {0!s}'
    e10010 = 'Resource Error: Confidence must be >= 0 and <=100. ({0!s}) is not in this range.'
    e10011 = 'Resource Error: Confidence must be of integer type. ({0!s}) is not an integer value.'
    e10012 = 'Resource Error: ({0!s}) was not found in id index.'
    e10013 = 'Resource Error: ({0!s}) was not found in name index.'
    e10020 = 'Resource Error: ID must be of integer type. ({0!s}) is not an integer value.'
    e10030 = 'Resource Error: Resource Type is not configured for this object.'
    e10040 = 'Resource Error: Cannot commit incomplete resource object.'
    e10050 = 'Resource Error: {0!s} is an invalid indicator.'
    e10060 = 'Resource Error: Type {0!s} must be a IndicatorType.'

    # Indicator Resource Object
    e10100 = 'Resource Error: DNS Active is not supported for this resource type.'
    e10110 = 'Resource Error: DNS Resolutions is not supported for this resource type.'
    e10120 = 'Resource Error: File Occurrences is not supported for this resource type.'
    e10130 = 'Resource Error: Size is not supported for this resource type.'
    e10140 = 'Resource Error: WhoIs Active is not supported for this resource type.'
    e10150 = 'Resource Error: File Occurrences is not supported for this resource type.'

    # Group Resource Object
    e10200 = 'Resource Error: Body is not supported for this resource type.'
    e10210 = 'Resource Error: Contents is not supported for this resource type.'
    e10220 = 'Resource Error: Event Date is not supported for this resource type.'
    e10230 = 'Resource Error: File Name is not supported for this resource type.'
    e10240 = 'Resource Error: File Size is not supported for this resource type.'
    e10250 = 'Resource Error: File Text is not supported for this resource type.'
    e10260 = 'Resource Error: File Type is not supported for this resource type.'
    e10265 = 'Resource Error: First Seen is not supported for this resource type.'
    e10270 = 'Resource Error: From is not supported for this resource type.'
    e10280 = 'Resource Error: Header is not supported for this resource type.'
    e10290 = 'Resource Error: Score is not supported for this resource type.'
    e10300 = 'Resource Error: Subject is not supported for this resource type.'
    e10310 = 'Resource Error: To is not supported for this resource type.'
    e10320 = 'Resource Error: Download is not supported for this resource type.'
    e10330 = 'Resource Error: Upload is not supported for this resource type.'

    # Victim Resource Object
    e10500 = 'Resource Error: Account is not supported for this resource type.'
    e10510 = 'Resource Error: Address is not supported for this resource type.'
    e10520 = 'Resource Error: Address Type is not supported for this resource type.'
    e10530 = 'Resource Error: Network is not supported for this resource type.'
    e10540 = 'Resource Error: Phone Type is not supported for this resource type.'
    e10550 = 'Resource Error: ({0!s}) is an Invalid Victim Asset Type.'
    e10560 = 'Resource Error: Website is not supported for this resource type.'

    #
    # API Errors
    #
    e80000 = 'API Error: {0!s}'

    #
    # Runtime Errors
    #
    e90000 = 'Resource object is not properly formatted.  Missing get_id or get_name methods.'
    e90001 = 'API returned failed status code.'
