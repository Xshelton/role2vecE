import pandas as pd
df=pd.read_csv('BIOGRID-ALL-4.1.190(no repeate)477444.csv')
geneA=df['geneA']
geneB=df['geneB']
def check_double():
 flag=0
 list_remove_double=[]
 for i in range(0,len(df)):
    if geneA[i]==geneB[i]:
        print('double found')
        flag=1
        print(geneA[i],geneB[i])
    else:
        list_remove_double.append({'geneA':geneA[i],'geneB':geneB[i]})
        
 if flag==0:
       print(' no double found out')
 return list_remove_double
listDD=check_double()
listDD=pd.DataFrame(listDD)
listDD.to_csv('BIOGRID-ALL-4.1.190(no repeate){}.csv'.format(len(listDD)),index=None)