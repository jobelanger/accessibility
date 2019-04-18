"""
Errors log

I have points of origin (origin_test) which are in lat/long format in a csv file.
I want to add these origin points as new nodes to my Puerto Rico road network, created through Pandana:
    https://github.com/gracedoherty/accessibility/blob/master/pandana_puertorico.py
"""

In [1]: origin_test = pd.read_csv('wpop_arec.csv')
origin_test.head()
Out[1]: 
       wpop  xmid xxmunicipi  xxcsi_mig0  xxcsi_mig1  xwpopm  adj_pop
0  1.278938     6    Arecibo    88019.09     82291.0   95583      NaN
1  1.295494     6    Arecibo    88019.09     82291.0   95583      NaN
2  1.380670     6    Arecibo    88019.09     82291.0   95583      NaN
3  1.366615     6    Arecibo    88019.09     82291.0   95583      NaN
4  1.355771     6    Arecibo    88019.09     82291.0   95583      NaN

network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-35-5078f2c7afff>", line 1, in <module>
    network.add_nodes_from(origin_test)

AttributeError: 'Network' object has no attribute 'add_nodes_from'




In [2]: network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-37-5078f2c7afff>", line 1, in <module>
    network.add_nodes_from(origin_test)

AttributeError: 'Network' object has no attribute 'add_nodes_from'




In [3]: nx.network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-38-c02e779e560e>", line 1, in <module>
    nx.network.add_nodes_from(origin_test)

AttributeError: module 'networkx' has no attribute 'network'




In [4]: network_gdf.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-39-b87494bc8376>", line 1, in <module>
    network_gdf.add_nodes_from(origin_test)

  File "C:\Users\grace\Anaconda3\envs\puerto0\lib\site-packages\pandas\core\generic.py", line 5067, in __getattr__
    return object.__getattribute__(self, name)

AttributeError: 'DataFrame' object has no attribute 'add_nodes_from'




In [5]: nx.network_gdf.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-40-e8905648a433>", line 1, in <module>
    nx.network_gdf.add_nodes_from(origin_test)

AttributeError: module 'networkx' has no attribute 'network_gdf'