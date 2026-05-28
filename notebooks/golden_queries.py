# for injectors only 
query1 = "how many wells are there?"
query2 = "What is the total water injection volume by year?"
query3 = "Tell me the mean yearly water injection volume for each subzone"
query4 = "rank wells by their variability (std) in water injection volume (the higher the grater the rank)?"
query5 = "whats the frequency of observations in the dataset (D, M, Y) ?"
query6 = "summarize the injection data"
query7 = "Which well had the single highest WATER_INJECTION_VOLUME reading at any point in time and what was that reading?"
query8 = "What is the average monthly injection volume per well grouped by NAME and MONTH?"
query9 = """For each SUBZONE compute the year-over-year percentage change in total injection 
volume and report the largest drop
"""
query1 = "how many wells are there?"
query1_2 = "what proportion of those are injectors"
query2 = "What is the total water injection volume by year?"
query3 = "Tell me the total water injection volume for each subzone each year"
query4 = "rank wells by their variability (std) in water injection volume (the higher the grater the rank)?"
query4_1 = "whats the highest ranked well?"
query5 = "whats the frequency of observations in the dataset (D, M, Y) ?"
query6 = "summarize the injection data"
query7 = "Which well had the single highest WATER_INJECTION_VOLUME reading at any point in time and what was that reading?"
query8 = "What is the average monthly injection volume per well grouped by NAME and MONTH?"
query9 = """For each SUBZONE compute the year-over-year percentage change in total injection 
volume and report the largest drop
"""
query10 = "For each injector well, calculate its total water injection volume and join it with the well location information. Return a table with the well name, total injected water, latitude, longitude, and any available location/type fields."
query11="Create two separate tables: one ranking injector wells by total water injection volume, and another ranking producer wells by total oil production volume."
 
golden_injector_queries = [query1, query1_2, query2, query3, query4, query4_1, 
                  query5, query6, query7, query8, query9, query10, query11
                ]
