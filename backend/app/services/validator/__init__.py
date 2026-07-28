"""CaseOS Validator service.

Pipeline position:

    VisionAnalyzer -> Validator -> Database

Every analysis JSON must pass through CaseOSValidator before it can
be persisted to the database.
"""
