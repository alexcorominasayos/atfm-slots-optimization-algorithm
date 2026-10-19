To execute the final results of the GDP model:
- Run AssignSlotsGDP.py
- Close the 2 graphs that appear
- A message will appear: "Print the non-regulated slots?" yes or no
Emissions and cost results will appear.
- A message will appear: "Print other interesting data?" yes or no
- Close the graph
- "Print slots after cancelling the ones with more than 2 hours of delay?" yes or no
Delay range results will appear
- "Plot delay pie?" yes or no

To execute the final results of the GHP model: 
- Run GHP.py
- Close the 2 graphs that appear
- A message in the console will appear: "Print the non-regulated slots?" No
- "Print other interesting data?" No
- Close the graph
- "Print slots after cancelling the ones with more than 2 hours of delay?" No
- "Plot delay pie?" No
Three solutions will appear, each with its respective minimization objective. 
The first corresponds to delay minimization (not included in the report as said  in the slides), the second to emissions minimization, and the third to cost minimization.

To find the results of the intermodality study:
Depending on: if GDP or GHP is applied follow the previous steps
- The files with clear names like "SubstitutedFlights" or "ComputeCost_GHP" give what they say
- File "compare_train_air" gives info about D2D and CO2 emissions with the graph (GDP)
- File "compute_delay_reduction_train" delay reduction without reassigning flights (GDP)
- File "CompareDelayReduction(_GHP)" delay reduction reassigning flights (GDP/GHP)