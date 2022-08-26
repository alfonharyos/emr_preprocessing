import pandas as pd
import json
import re

class preprocess:
    
  def low(self,text):
    text = text.lower()
    return text

  def del_punc(self,text):
    text = text.replace("x000d", "")
    text = re.sub(r'[!"#$%&\'()*/:;<=>?@[\]^_`{|}~]+', "", text)
    return text

  def del_num(self,text):
    text = re.sub(r'\b[0-9]+\b\s*', '', text)
    return text
  
  def replace_param(self,text):
    # replace newline ==> koma
    text = text.replace("\n",",")
    # memberi space pada parameter penentuan gejala sebelum melakukan pembagian gejala
    # pemberian space pada parameter dengan menggunakan metode berbeda karena dg terkandung juga didalam dengan
    if 'dg' in text or 'riw' in text :
      txt = []
      for w in text.split():
        if w == 'dg': 
          w = 'dengan'
        elif w == 'riw':
          w = 'riwayat'
        else : w=w
        txt.append(w)
      text = ' '.join(txt)
    # normalisasi kata yg berkaitan dengan gejala
    text = text.replace("dgn", "dengan")
    text = text.replace("dengan", ", dengan ")
    text = text.replace("riwayat", "riwayat ")
    text = text.replace("sjk", "sejak")
    text = text.replace("sejak", "sejak ")
    text = text.replace("diagnosis", "diagnosa ")
    text = text.replace("mengeluhkan", "keluhan")
    text = text.replace("mengeluh", "keluhan")
    text = text.replace("keluhan", "keluhan ")
    text = text.replace("tdk", "tidak")
    text = text.replace("tidak", ", tidak ")
    text = text.replace(' + ', " + dengan ")
    text = text.replace('+', " +,")
    text = text.replace('-', " -,")
    text = text.replace(',', " ,")
    text = text.replace('.', " .")
    return text

  def stop_w(self,text,param_s,param_d,param_b,param_n):
    list_chr_penting = ['ulu', 'ibu', 'di'] # singkatan 2-3 char yang penting(tidak dihapus)
    # stopword Indonesia
    with open('filter_emr/stopword-id_tala.txt', 'r') as s:                           
      stopword = [line.strip() for line in s]
    with open('filter_emr/add_stopword-id.txt', 'r') as add_s:
      stopword = stopword+[line.strip() for line in add_s]
      stopword = [word for word in stopword if word not in param_s+param_d+param_b+param_n+list_chr_penting]
    # singkatan yg tidak perlu
    list_chr = ['yg', 'yg ll', 'dr', 'sda', 'rs']
    txt = ' '.join([word for word in text.split() if word not in list_chr+stopword])
    return txt

  def ubah(self,text):
    list_chr_penting = ['ulu', 'ibu', 'di'] # singkatan 2-3 char yang penting(tidak dihapus)
    singkatan_dict = json.load( open( "filter_emr/singkatan_dict.json" ) ) # open dictionary

    list_acro = list()
    for key in singkatan_dict.keys():
      list_acro.append(key)

    txt = []
    for w in text.split():
      if (len(w) == 3 or len(w) == 2) and not w.isnumeric() and w not in list_chr_penting:
        if w in list_acro:
          w = singkatan_dict.get(w, w) # merubah singkatan
        elif w not in list_acro : w=None
      elif w in list_acro:
        w = singkatan_dict.get(w, w) # merubah singkatan
      else: w=w
      txt.append(w)
    txt = ' '.join(list(filter(None, txt)))
    return txt.lower()

  def split_txt(self,text):
    text = re.split('[.,]',text)
    return text

  def gejala(self,text,param_s,param_d,param_b,param_n,n):
    txt = []
    for s in text:
      # Memilah kalimat yang tidak mengandung negasi
      if any(set(s.split()) & set(param_n)) == False:

        # Parameter terletak sebelum gejala
        if any(set(s.split()) & set(param_d+param_s)) == True:
          # Mencari index parameter yang paling dekat dengan target
          ind=[]
          for p in param_d+param_s:
            if p in s:
              indices = [index for index, element in enumerate(s.split()) if element == p]
              ind.extend(indices)
          ind=max(ind)
          # ambil n kata setelah parameter
          try:
            x = ind+n
            if s.split()[ind] in param_d:
              s = ' '.join(s.split()[ind+1:x+1])
            else:
              s = ' '.join(s.split()[ind:x])
            # hapus paramter lain yang ada di dalam kalimat
            for pb in param_b:
              if pb in s:
                s = s.split()
                ind = s.index(pb)
                # hapus kata" setelah parameter
                del s[ind:]
                s = ' '.join(s)
            txt.append(s)
          except ValueError:
            pass

        # Parameter terletak setelah gejala
        elif any(set(s.split()) & set(param_b+param_s)) == True:
          for p in param_b:
            if p in s:
              try:
                # mencari index dari parameter di dalam kalimat
                ind = s.split().index(p)
                # ambil n kata sebelum parameter
                x = ind-n
                if x < 0 : x=0
                if s.split()[ind] in param_s:
                  s = ' '.join(s.split()[x:ind+1])
                else:
                  s = ' '.join(s.split()[x:ind])
                # hapus paramter lain yang ada di dalam kalimat
                for pd in param_d:
                  if pd in s:
                    s = s.split()
                    ind = s.index(pd)
                    # hapus kata" sebelum parameter
                    del s[0:ind+1]
                    s = ' '.join(s)
                txt.append(s)
              except ValueError:
                pass
        
    txt = list(filter(None, txt))
    return txt

  def get_symptoms( self, text:str,
                    param_s:str='luka;nyeri;sakit', 
                    param_d:str='diagnosa;keluhan;dengan;riwayat', 
                    param_b:str='sejak;+',
                    param_n:str='tidak;-', n:int=5):
    param_s = [w.strip() for w in param_s.split(';')]
    param_d = [w.strip() for w in param_d.split(';')]
    param_b = [w.strip() for w in param_b.split(';')]
    param_n = [w.strip() for w in param_n.split(';')]
    text = self.low(text)
    text = self.del_punc(text)
    text = self.del_num(text)
    text = self.replace_param(text)
    text = self.stop_w(text,param_s,param_d,param_b,param_n)
    text = self.ubah(text)
    text = self.split_txt(text) 
    text = self.gejala(text,param_s,param_d,param_b,param_n,n)
    if text == []:
      text = None
    return text 
