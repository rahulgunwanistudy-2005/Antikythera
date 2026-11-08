"""Explicit external-list overlap, without substituting an abstract's count for gold."""

def yarnell_overlap(extracted_names, reference_names=None, *, reference_verified=False,
                    reference_source=None, counting_unit='plant_name_as_written'):
    """Score a supplied verified reference list; never reconstruct 105 labels.

    Caller must reconcile counting units and nomenclature first. Only whitespace
    and case normalization is applied here; no undocumented synonym mapping.
    """
    valid_units={'plant_name_as_written','species','genus'}
    if counting_unit not in valid_units:raise ValueError('Explicit supported counting unit required.')
    def normalize(names):
        if not isinstance(names,(list,tuple,set)) or any(not isinstance(n,str) or not n.strip() for n in names):
            raise ValueError('Each name list must contain nonempty strings.')
        return {' '.join(n.casefold().split()) for n in names}
    extracted=normalize(extracted_names)
    base={'counting_unit':counting_unit,'extracted_count':len(extracted),
          'reference_source':reference_source,
          'normalization':'Case and whitespace only; caller must harmonize taxonomy and counting unit.'}
    if reference_names is None or reference_verified is not True or not reference_source:
        return dict(base,status='pending',reason='A verified reference list with provenance is required; the published total of 105 is not a gold list.')
    reference=normalize(reference_names)
    if not reference:return dict(base,status='pending',reason='Verified reference list is empty.')
    common=extracted&reference
    return dict(base,status='computed',reference_count=len(reference),overlap_count=len(common),
                reference_recall=len(common)/len(reference),extraction_list_precision=len(common)/len(extracted) if extracted else None,
                jaccard=len(common)/len(extracted|reference),overlap=sorted(common),
                missing_reference_names=sorted(reference-extracted),extra_extracted_names=sorted(extracted-reference))
