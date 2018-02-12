def populate():
	#Create Clients
	mce = Client(name='Marin Clean Energy', domain="marincleanenergy.org", abbreviation='MCE')
	scp = Client(name='Sonoma Clean Power', domain="sonomacleanpower.org", abbreviation='SCP')
	pce = Client(name='Peninsula Clean Energy', domain="peninsulacleanenergy.com", abbreviation='PCE')
	svce = Client(name='Silicon Valley Clean Energy', domain="siliconvalleycleanenergy.org", abbreviation='SVCE')

	[db_session.add(x) for x in [mce,scp,pce,svce]]
	db_session.commit()


	#Create Heirarchy Version for Budget
	for client in db_session.query(Client):
		hv = HeirarchyVersion(client_id=client.id, name='Budget',description="Default Heirarchy for Budget and Dashboard",levels=['department','budget_line','gl_account'])
		db_session.add(hv)
		
	db_session.commit()


	##
	## Load SCP Budget Heirarchy Data

	depts = data.scp.account_map.budget_department.dropna().drop_duplicates()
	line = data.scp.account_map.loc[:,['budget_department','budget_line']].dropna().drop_duplicates()
	gl = data.scp.account_map.loc[:,['budget_line','account_id']].dropna().drop_duplicates()


	#load budget heirarchy
	for b in depts:
		bn = HeirarchyNode(client_id=2, name=b) #parent=get_or_create(db_session, BudgetNode, name = b)
		db_session.add(bn)

	db_session.commit()
			
	for a,b in line.iterrows():
		#print(b['budget_line'])
		parent = get_or_create(db_session, HeirarchyNode, name = b['budget_department'])
		bn = HeirarchyNode(client_id=2, name=b['budget_line'], parent=parent)
		db_session.add(bn)

	db_session.commit()
		
	for a,b in gl.iterrows():
		#print(b[1])
		parent = get_or_create(db_session, HeirarchyNode, name = b[0])
		bn = HeirarchyNode(client_id=2, name=b[1], parent=parent)
		db_session.add(bn)

	db_session.commit()

	db_session.close()
