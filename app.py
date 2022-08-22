import pandas as pd
import streamlit as st
import xlsxwriter
from filter_emr.filter import preprocess as pp
from io import BytesIO
from st_aggrid import AgGrid

PAGE_CONFIG = {"page_title":"EMR-Preprocessing-App", "page_icon":"hospital", "layout":"wide"}
st.set_page_config(**PAGE_CONFIG)

def up_file(uploaded_file):
    with st.spinner('Wait for it...'):
        if uploaded_file.name[-3:] == 'csv':
            df = pd.read_csv(uploaded_file)
            typ = 'csv'
        elif (uploaded_file.name[-3:] == 'xls') or (uploaded_file.name[-4:] == 'xlsx'):
            df = pd.read_excel(uploaded_file) 
            typ = 'xlsx'
        df = df.astype(str)
    return df, typ

def update_counter():
        st.session_state.keluhan = st.session_state.col
        st.session_state.param_sakit = st.session_state.sakit
        st.session_state.param_awal = st.session_state.awal
        st.session_state.param_akhir = st.session_state.akhir
        st.session_state.param_neg = st.session_state.neg

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

if uploaded_file != None:   
    if 'df_up' not in st.session_state:
        st.session_state.df_up, st.session_state.data_type = up_file(uploaded_file)

    st.header('EMR Display')
    with st.spinner('Wait for display...'):
        if 'extract_gejala' in st.session_state.df_up.columns: 
            AgGrid(st.session_state.df_up.\
                    drop(['extract_gejala'], axis=1).\
                    reset_index(), theme='streamlit')

        else: 
            AgGrid(st.session_state.df_up.\
                    reset_index(), theme='streamlit')

    # preprocessing
    if 'keluhan' not in st.session_state:
        st.session_state.keluhan = None
        st.session_state.param_sakit = 'luka;sakit;nyeri'
        st.session_state.param_awal = 'diagnosa;keluhan;dengan;riwayat;kontrol'
        st.session_state.param_akhir = 'sejak;+'
        st.session_state.param_neg = 'tidak;-'   
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
            AgGrid(df_emr_pp[[st.session_state.keluhan,'extract_gejala']].astype(str).reset_index(), theme='streamlit')
            
        st.download_button(
            label="Download Data",
            data=st.session_state.dl_data,
            file_name='EMR_preprocessing.'+st.session_state.data_type
        )

else:
    st.warning('you need to upload a csv or excel file.')
    
