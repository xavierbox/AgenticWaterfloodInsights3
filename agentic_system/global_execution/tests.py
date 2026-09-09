import sys, os 
import pandas as pd 
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')


from agentic_system.common.get_llm import * 
from agentic_system.common.base_plan import PlannerComponent, PlannerConfig
from agentic_system.global_execution.execution_plan_template import ExecutionPlanTemplate
from agentic_system.global_execution.global_execution_prompt import prompt 






def test_planner( planner ):
    import pandas as pd
    pd.set_option("display.max_colwidth", None)

    # ``agent`` is a string for the usual single-agent route and a list only when
    # the request genuinely requires more than one specialist.
    planner_golden_questions = [
        {
            "id": "query0_0",
            "agent": "direct_answer",
            "query": "Why can a high water cut be a problem even when total liquid production remains high?",
        },
        {
            "id": "query0_1",
            "agent": "results_interpreter",
            "query": "Which wells are performing badly?",
        },
        {
            "id": "query1_1",
            "agent": "input_data_analysis",
            "query": "plot the liquid injection rates in sector 1 over time",
        },
        {
            "id": "query1_2",
            "agent": "input_data_analysis",
            "query": "list the 3 wells with the highest watercut",
        },
        {
            "id": "query1_3",
            "agent": "input_data_analysis",
            "query": "plot the VRR split by sector",
        },
        {
            "id": "query1_4",
            "agent": "input_data_analysis",
            "query": "Define VRR and plot the VRR over time for sectors 1, 2, and 3",
        },
        {
            "id": "query1_5",
            "agent": "input_data_analysis",
            "query": "Is the data frequency daily or monthly?",
        },
        {
            "id": "query1_6",
            "agent": "input_data_analysis",
            "query": "Which sector had the largest increase in water injection over the last two years, and did its oil production increase over the same period?",
        },
        {
            "id": "query2_1",
            "agent": "results_interpreter",
            "query": "Why weren't 12 of the initially screened wells modelled?",
        },
        {
            "id": "query2_2",
            "agent": "results_interpreter",
            "query": "Which is the best injector in terms of utility?",
        },
                {
            "id": "query2_21",
            "agent": "results_interpreter",
            "query": "Which is the best injector?",
        },
        {
            "id": "query2_3",
            "agent": "results_interpreter",
            "query": "Which producer is best supported?",
        },
        {
            "id": "query2_4",
            "agent": "results_interpreter",
            "query": "Summarize the quality of the models.",
        },
        {
            "id": "query2_5",
            "agent": "results_interpreter",
            "query": "Is there any evidence of thief zones?",
        },
        {
            "id": "query2_6",
            "agent": "results_interpreter",
            "query": "Plot the observed and simulated liquid rates for all wells.",
        },
        {
            "id": "query2_7",
            "agent": "results_interpreter",
            "query": "Is there any evidence of aquifer support?",
        },
        {
            "id": "query2_8",
            "agent": "results_interpreter",
            "query": "Did we use BHP in the simulation?",
        },
        {
            "id": "query2_9",
            "agent": "results_interpreter",
            "query": "Rank the injectors based on their utility.",
        },
        {
            "id": "query2_10",
            "agent": "results_interpreter",
            "query": (
                "For every producer, select three or four points from its production "
                "history and plot observed versus simulated liquid production at those points."
            ),
        },
        {
            "id": "query2_11",
            "agent": "results_interpreter",
            "query": "Give me a summary of the results, focusing on support and channeling.",
        },
        {
            "id": "query2_12",
            "agent": "results_interpreter",
            "query": "Which producers appear poorly supported by injection, and how reliable is that conclusion given their history-match quality?",
        },
        {
            "id": "queryb_1",
            "agent": ["input_data_analysis", "results_interpreter"],
            "query": "Which 10 producers have the highest oil-to-water ratio, and which injectors support them, if any?",
        },
        {
            "id": "query3_1",
            "agent": "scenario_analyst",
            "query": "I need to shut in well AB. Analyze the consequences and give me concrete actions.",
        },
        {
            "id": "query3_2",
            "agent": "results_interpreter",
            "query": "Summarize the results.",
        },
        {
            "id": "query3_3",
            "agent": "results_interpreter",
            "query": "Is there any evidence of channeling?",
        },
        {
            "id": "query3_4",
            "agent": "scenario_analyst",
            "query": "What will happen if I reduce the injection rate in well AB by 30%?",
        },
        {
            "id": "query3_5",
            "agent": "scenario_analyst",
            "query": "If injector I12 is shut in, which producers are most likely to be affected and which other injectors could compensate for the lost support?",
        },
        {
            "id": "query4_1",
            "agent": "opportunity_scanner",
            "query": "How can I optimize my waterflood? Give me concrete actions.",
        },
        {
            "id": "query4_2",
            "agent": "opportunity_scanner",
            "query": "I need to reduce water production. Give me concrete actions.",
        },
        {
            "id": "query4_3",
            "agent": "opportunity_scanner",
            "query": "Identify injectors where injection could potentially be reduced with the lowest expected impact on supported oil production.",
        },
    ]


    results = []
    for n,question in enumerate(planner_golden_questions):#[6:10]:
        print(f"Running test for question [{n}]: {question['query']}")

        query = question['query']
        #response = agent.invoke({
        #        "messages": [
        #            {"role": "user", "content": query}
        #        ]
        #    })['structured_response']
        response = planner.run( query )

        agent_names = ",".join([task.agent for task in response.tasks])

        results.append({
            
            "id": question['id'],
            "query": query,
            "expected_agent": question['agent'] if isinstance(question['agent'], str) else ",".join(question['agent']),
            "actual_agent": agent_names,
            "user_intent": response.user_intent,
            "success": agent_names == (question['agent'] if isinstance(question['agent'], str) else ",".join(question['agent'])),
            #"tasks": [task.dict() for task in response.tasks]
        })


    df = pd.DataFrame( results )
    df = df[ ['success'] + list(df.columns[0:-1]) ] 
    print( df ) 
    return df 



llm = azure_llm_if()
config  = PlannerConfig( prompt=prompt)#, response_format=ToolStrategy(ExecutionPlanTemplate) )
planner = PlannerComponent( llm=llm, config=config, plan_model=ExecutionPlanTemplate )

results = test_planner(planner)
print(results)


from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
output_file_path = SCRIPT_DIR / "planner_test_results.csv"
results.to_csv(output_file_path, index=False)

