import numexpr

def evaluate_expression(df, expression, col_map={}):
    """evaluates a numexpr expression using variables named after
    columns in the dataframe. you can use variable names that differ
    from the column names by specifying the mapping in col_map. For example
    df = pd.DataFrame({
        'foobar': [1,2,3],
        'bazquux': [4,5,6]
    })
    evaluate_expression('foobar + a', col_map={
        'bazquux': 'a'
    })
    """
    # apply col_name mappings, if any
    local_dict = {}
    for col_name, values in df.to_dict('series').items():
        if col_name in col_map:
            col_name = col_map[col_name]
        local_dict[col_name] = values
    # evaluate the expression
    values = numexpr.evaluate(expression, local_dict=local_dict)
    # return the results as a series, indexed the same as the dataframe
    return pd.Series(values, index=df.index)

def compute_flags(df, flag_expressions, col_map={}):
    # flag expressions should be a dict, and it should
    # be an OrderedDict to get columns in specified order
    # (flagname, expression)
    # returns a dataframe
    d = OrderedDict()
    for flagname, expression in flag_expressions.items():
        values = evaluate_expression(df, expression, col_map=col_map)
        d[flagname] = values
    return pd.DataFrame(d)
