def current_state_to_record(state, step = None) -> pd.DataFrame:
    df = state['particles_info']\
    .groupby(by = ['side', 'type'])\
    .size().unstack(fill_value=0)
    df.columns.name = None
    d = {
        type_:key for key, type_ 
        in zip(PARTICLE_ATTR.keys(),
        [
            ATTR['type'] for ATTR in PARTICLE_ATTR.values()
            ]
        )
    }
    df.rename(columns = d, inplace = True)
    df['energy'] = state['energy']
    df['volume'] = state['volume']
    if step is not None:
        df['step'] = step
    df = df.reset_index()
    return df
