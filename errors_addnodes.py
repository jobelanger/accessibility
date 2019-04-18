"""
Errors log

I have points of origin (origin_test) which are in x,y format in a csv file.
I want to add these origin points as new nodes to my Puerto Rico road network, created through Pandana:
    https://github.com/gracedoherty/accessibility/blob/master/pandana_puertorico.py
"""

In [31]: origin_test.head()
Out[31]: 
       wpop  xmid xxmunicipi  xxcsi_mig0  ...  xwpopm  adj_pop          X          Y
0  1.278938     6    Arecibo    88019.09  ...   95583      NaN -66.636840  18.493133
1  1.295494     6    Arecibo    88019.09  ...   95583      NaN -66.636007  18.493133
2  1.380670     6    Arecibo    88019.09  ...   95583      NaN -66.627674  18.493133
3  1.366615     6    Arecibo    88019.09  ...   95583      NaN -66.624341  18.493133
4  1.355771     6    Arecibo    88019.09  ...   95583      NaN -66.623507  18.493133

network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-35-5078f2c7afff>", line 1, in <module>
    network.add_nodes_from(origin_test)

AttributeError: 'Network' object has no attribute 'add_nodes_from'




In [32]: network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-37-5078f2c7afff>", line 1, in <module>
    network.add_nodes_from(origin_test)

AttributeError: 'Network' object has no attribute 'add_nodes_from'




In [33]: nx.network.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-38-c02e779e560e>", line 1, in <module>
    nx.network.add_nodes_from(origin_test)

AttributeError: module 'networkx' has no attribute 'network'




In [34]: network_gdf.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-39-b87494bc8376>", line 1, in <module>
    network_gdf.add_nodes_from(origin_test)

  File "C:\Users\grace\Anaconda3\envs\puerto0\lib\site-packages\pandas\core\generic.py", line 5067, in __getattr__
    return object.__getattribute__(self, name)

AttributeError: 'DataFrame' object has no attribute 'add_nodes_from'




In [35]: nx.network_gdf.add_nodes_from(origin_test)
Traceback (most recent call last):

  File "<ipython-input-40-e8905648a433>", line 1, in <module>
    nx.network_gdf.add_nodes_from(origin_test)

AttributeError: module 'networkx' has no attribute 'network_gdf'
