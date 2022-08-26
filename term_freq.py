import pandas as pd

def symp(df, extract_gejala_column_name, diagnosa_column_name, diagnosa):
    df = df.loc[df[diagnosa_column_name] == diagnosa]
    symps=[]
    for k in df[extract_gejala_column_name]:
        if k != None:
            for symp in k:
                symps.append(symp)
    df_gejala = pd.DataFrame(symps, columns=['gejala'])
    df_diagnosa = pd.DataFrame(columns=['diagnosa'])
    df_gejala = pd.concat([df_diagnosa, df_gejala], axis=1) # concat 
    df_gejala.diagnosa = df_gejala.diagnosa.fillna(diagnosa)
    return df_gejala

def freq_gejala(df, extract_gejala_column_name, diagnosa_column_name):
    df_gejala_all=pd.DataFrame(columns=['diagnosa','gejala'])
    for diagnosa in df[diagnosa_column_name].unique().tolist():
        df_gejala = symp(df, extract_gejala_column_name, diagnosa_column_name, diagnosa)
        df_gejala_all = pd.concat([df_gejala_all, df_gejala], axis=0)
    return df_gejala_all
