def loadValidation(f,typesloads,l):
    for key, load in f.items():
        # 1. Check if start position 'a' is on the beam
        if not (0 <= load['a'] <= l):
            raise ValueError(f"Error in '{key}': Start position 'a' ({load['a']}) is outside the beam limits [0, {l}].")
        
        # 2. Check if end position 'a1' is on the beam (if it applies)
        if load['type'] in typesloads[1:4]: # Distributed loads need 'a1'
            if 'a1' not in load:
                raise ValueError(f"Error in '{key}': Distributed loads require an 'a1' coordinate.")
            if not (0 <= load['a1'] <= l):
                raise ValueError(f"Error in '{key}': End position 'a1' ({load['a1']}) is outside the beam limits [0, {l}].")
            if load['a'] >= load['a1']:
                raise ValueError(f"Error in '{key}': Start position 'a' must be strictly less than end position 'a1'.")