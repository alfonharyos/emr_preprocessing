import pandas as pd
import streamlit as st
import xlsxwriter
import openpyxl
from filter_emr.filter import preprocess as pp
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


PAGE_CONFIG = {"page_title":"EMR-Preprocessing-App", "page_icon":"hospital", "layout":"wide"}
st.set_page_config(**PAGE_CONFIG)

def up_file(uploaded_file):
    with st.spinner('Wait for it...'):
        if uploaded_file.name[-3:] == 'csv':
            df = pd.read_csv(uploaded_file)
            typ = 'csv'
        elif uploaded_file.name[-3:] == 'xls':
            df = pd.read_excel(uploaded_file) 
            typ = 'xls'
        elif uploaded_file.name[-4:] == 'xlsx':
            df = pd.read_excel(uploaded_file, engine="openpyxl") 
            typ = 'xlsx'
        df = df.astype(str)
    return df, typ

def del_ss():
    for key in st.session_state.keys():
        del st.session_state[key]

def display_table(df: pd.DataFrame) -> AgGrid:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True,)
    gb.configure_selection('single')
    return AgGrid(
        df,
        gridOptions=gb.build(), theme='streamlit',
        update_mode=GridUpdateMode.MODEL_CHANGED
        )

def update_counter():
        st.session_state.keluhan = st.session_state.col
        st.session_state.param_sakit = st.session_state.sakit
        st.session_state.param_awal = st.session_state.awal
        st.session_state.param_akhir = st.session_state.akhir
        st.session_state.param_neg = st.session_state.neg
        st.session_state.submit_count+=1

def convert_df(df, type):
    if type == 'csv':
        df = df.to_csv().encode('utf-8')
    elif (type == 'xls') or (type == 'xlsx'):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False) 
        writer.save() 
        df = output.getvalue()
    return df


st.title(' EMR Preprocessing ')
st.text('Ekstrasi gejala keluhan pasien')

uploaded_file = st.file_uploader('Choose EMR file', 
                                type=['csv','xlsx', 'xls'],
                                accept_multiple_files=False)

if uploaded_file:   

    if 'df_up' not in st.session_state:
        st.session_state.df_up, st.session_state.data_type = up_file(uploaded_file)
        
    # preprocessing
    if 'keluhan' not in st.session_state:
        st.session_state.param_sakit = 'luka;sakit;nyeri'
        st.session_state.param_awal = 'diagnosa;keluhan;dengan;riwayat;kontrol'
        st.session_state.param_akhir = 'sejak;+'
        st.session_state.param_neg = 'tidak;-'  
        st.session_state.submit_count = 0

    try:
        with st.form(key='my_form'):
            st.selectbox(   label='Pilih column keluhan pasien',
                            options=[None]+st.session_state.df_up.columns.tolist(),
                            help='Pilih column yang akan diekstrak',
                            index=0, key='col')
            st.write('Parameter (default)')
            with st.expander("Merubah Nilai Parameter"):
                st.text_input(  label='Parameter Sakit',
                                value=st.session_state.param_sakit,
                                help='Perameter sakit: tanda/kata yang mewakili target/gejala', 
                                key='sakit')
                st.text_input(  label='Parameter Awal', 
                                value=st.session_state.param_awal,
                                help='Perameter awal: tanda/kata yang letaknya berada sebelum target/gejala', 
                                key='awal')
                st.text_input(  label='Parameter Akhir', 
                                value=st.session_state.param_akhir,
                                help='Perameter akhir: tanda/kata yang letaknya berada setelah target/gejala', 
                                key='akhir')
                st.text_input(  label='Parameter Negatif', 
                                value=st.session_state.param_neg,
                                help='tanda/kata yang menandakan bahwa pasien tidak memiliki gejala',
                                key='neg')
            submit = st.form_submit_button(label='Extract', on_click=update_counter)
    except ValueError:
        st.warning('Pilih Kolom Keluhan')

    # Extrak Gejala
    if submit and (st.session_state.submit_count>1):
        del st.session_state.df_pp

    if submit:
        if 'df_pp' not in st.session_state:
            df_emr = st.session_state.df_up
            with st.spinner('Wait for it...'):
                df_emr['extract_gejala'] = df_emr[st.session_state.keluhan].\
                                                    apply(lambda x: pp().\
                                                    get_symptoms(str(x),
                                                    st.session_state.param_sakit,
                                                    st.session_state.param_awal,
                                                    st.session_state.param_akhir,
                                                    st.session_state.param_neg,
                                                    5))
                st.session_state.df_pp = df_emr
                st.session_state.dl_data = convert_df(df_emr, st.session_state.data_type)
    
    if 'df_pp' in st.session_state: 
        with st.spinner('Wait for display...'):
            df_emr_pp = st.session_state.df_pp
            display_table(df_emr_pp[[st.session_state.keluhan,'extract_gejala']].astype(str).reset_index())

        st.download_button(
            label="Download Data",
            data=st.session_state.dl_data,
            file_name='EMR_preprocessing.'+st.session_state.data_type
        )
else:
    st.warning('you need to upload a csv or excel file.')
    del_ss()
