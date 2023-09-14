from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Race Predictor')
st.write('This is a race predictor where you can simulate two types of races.')
st.write('A Team race or an Individual race. You can pick by selecting a tab.')
st.write('Go to the Race tab and then after enetering the teams or athletes you want to race')
st.write('Select the respective Visual tab to see how that race would pan out.')
 
