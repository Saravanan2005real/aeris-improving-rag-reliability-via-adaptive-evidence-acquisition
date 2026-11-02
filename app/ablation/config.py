from app.ablation.schemas import AblationVariant
from app.controller.schemas import ControllerConfig

def get_config_for_variant(variant: AblationVariant) -> ControllerConfig:
    """
    Map an AblationVariant to its respective ControllerConfig.
    """
    config = ControllerConfig()
    
    if variant == AblationVariant.FULL_AERIS:
        pass
    elif variant == AblationVariant.NO_ADAPTIVE_RETRIEVAL:
        config.enable_adaptive_retrieval = False
    elif variant == AblationVariant.NO_QUERY_REFORMULATION:
        config.enable_query_reformulation = False
    elif variant == AblationVariant.NO_RETRIEVAL_MEMORY:
        config.enable_retrieval_memory = False
    elif variant == AblationVariant.NO_CLAIM_VERIFICATION:
        config.enable_claim_verification = False
    elif variant == AblationVariant.NO_CONTRADICTION_ANALYSIS:
        config.enable_contradiction_analysis = False
    elif variant == AblationVariant.NO_CROSSLINGUAL_AGREEMENT:
        config.enable_cross_lingual_analysis = False
    elif variant == AblationVariant.NO_SELECTIVE_VERIFICATION:
        config.enable_selective_verification = False
        
    return config
