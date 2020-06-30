#dashboard dos estados

#####
##### chamadas de bibliotecas
#####

import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input,Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots #necessario, pela documentacao para a criacao de graficos com dois eixos
 
######
###### capturando os dados
######

enderecoAlterna="dadosTeste.xlsx"
compilado=pd.read_excel(enderecoAlterna,sheet_name="Compilado",index_col=0)
ICMS=pd.read_excel(enderecoAlterna,sheet_name="ICMS",index_col=0)
nomeMeses=["janeiro","fevereiro","março","abril","maio"]
beginner='CE' #estado que é plotado na abertura

print(ICMS)

#todosNomes é uma lista de lista, cada sublista conterá em 0 o label e em 1 o value
#para ser usado no dropdown da página
todosNomes=[]
for i in range(len(compilado.index.values)):
    todosNomes.append([compilado['UF_nome'][i],compilado.index.values[i]])


def retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado):

  #Criar uma lista para cada estado com os seguintes dados
  #0 - Nome dos Meses 
  #1 - ICMS de 2019 
  #2 - ICMS de 2020 
  #3 - ICMS acumulado 2019 
  #4 - ICMS acumulado 2020 
  #5 - diferencial absoluto dos ICMS's acumulados 
  #6 - diferencial percentual dos ICMS's acumulados 
  #7 - lista contendo as ajudas totais decorrentes de LC173_Recursos, LC173_Suspensão e MP938

  dadosEstado=[]
  NMeses=len(nomeMeses)

  dadosEstado.append(nomeMeses)

  selecao2019=list(range(0,NMeses))
  selecao2020=list(range(NMeses,NMeses*2))
  selecaoAjudas=list(range(1,4))

  dadosEstado.append(ICMS.loc[EstadoAlvo].iloc[selecao2019].tolist()) #adicionando os valores de ICMS de 2019
  dadosEstado.append(ICMS.loc[EstadoAlvo].iloc[selecao2020].tolist()) #adicionando os valores de ICMS de 2020

  #fazendo o acumulado de 2019 e de 2020 e os diferenciais absolutos e percentuais
  dadosEstado.append([])
  dadosEstado.append([])
  dadosEstado.append([])
  dadosEstado.append([])
  acumulado2019=0
  acumulado2020=0

  for i in range(NMeses):
      dadosEstado[3].append(acumulado2019+dadosEstado[1][i])
      acumulado2019=acumulado2019+dadosEstado[1][i]
      dadosEstado[4].append(acumulado2020+dadosEstado[2][i])
      acumulado2020=acumulado2020+dadosEstado[2][i]
      dadosEstado[5].append(acumulado2020-acumulado2019)
      dadosEstado[6].append(100*(acumulado2020/acumulado2019-1)) #x 100 para plotar o %

  #adicionando os auxílios recebidos
  dadosEstado.append(compilado.loc[EstadoAlvo].iloc[selecaoAjudas].tolist())

  return dadosEstado

  

def retonarDf(EstadoAlvo,nomeMeses,ICMS,compilado):
  #vai retornar uma lista de dataFrames, com a seguinte estrutura
  # 0 - dataframe contendo os dados de recursos recebidos, MP e LC 173 e de suspensão de dívida
  # 1 - dataframe contendo os dados de total e de icms perdido até agora
  # 2 - dataframe contendo o índice de suficiencia
  listadeDF=[]
  #primeiro item
  dadosEstado=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado)
  dataF = pd.DataFrame({'Recursos MP938': [dadosEstado[7][0]],
                   'Recursos LC 173': [dadosEstado[7][1]],
                   'Suspensão de Dívida LC173': [dadosEstado[7][2]]}, index=[EstadoAlvo])
  listadeDF.append(dataF)
  #segundo item
  dataF = pd.DataFrame({'Suporte Financeiro': [sum(dadosEstado[7])],
                   'ICMS Perdido': [dadosEstado[5][-1]]}, index=[EstadoAlvo])
  listadeDF.append(dataF)
  #terceiro item
  if dadosEstado[5][-1] >= 0 :
    dataF = pd.DataFrame({'Suficiência do Suporte': ['Não perdeu arrecadação.']}, index=[EstadoAlvo])  
  else:
    dataF = pd.DataFrame({'Suficiência do Suporte': [-1*sum(dadosEstado[7])/dadosEstado[5][-1]]}, index=[EstadoAlvo])
  
  listadeDF.append(dataF)
  return listadeDF


####
####
#### SITE
####
####


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server=app.server #li em um tutorial q era necessario p o heroku
app.title='LC 173 Monitora'
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'}) #Bootstrap CSS

#
# estilos para o layout
#
tabelaTop = { 'align-items': 'center' }
tabelasEstilo = { 'vertical-align': 'cmiddle'}

#

#o layout vai conter todos os componentes do site, html e componentes dash
app.layout = html.Div(

  html.Div([
    #
    #primeira linha contendo o head
    #
    html.Div([

      html.H1(children='Monitoramento do Suporte aos Estados',className='nine columns'),

      html.Img(
        src="data:image/jpeg;base64,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",
        className='three columns',
        style={
          'height': '14%',
          'width': '14%',
          'float': 'right',
          'position': 'relative',
          'margin': 20 },
              )

    ], className = 'row' ), # fim da primeira linha

    #
    #segunda linha contendo o dropdown
    #
    html.Div([
      #menu dropdown com a id para ser acessado via callback e a lista de opções geradas a partir do dataframe
      dcc.Dropdown(
          id='uf-dropdown',
          options=[{'label':i[0],'value':i[1]} for i in todosNomes],
          value=beginner,
          clearable=False
      )
    ], className = 'row'), # fim da segunda linha

    #
    #terceira linha contendo o gráfico e a tabela
    #

    html.Div([

      #div para a exibição do gráfico. Repare que o elemento graph só tem o ID, o gráfico será gerado no callback
      html.Div([
         dcc.Graph(id='meu-grafico-aqui')],className= 'eight columns'),
      #tabela contendo os dados
      html.Div([

          dash_table.DataTable(
            id='tabelaSuficiencia',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[2].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[2].to_dict('records'),
            style_cell={'textAlign': 'center'}  ) ], style=tabelasEstilo, className= 'four columns' )

    ], className='row'), # fim da terceira linha

    #
    #quarta linha contendo as tabelas com os detalhes
    #

    html.Div([

        dash_table.DataTable(
            id='tabelaRecursos',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[0].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[0].to_dict('records'),
            style_cell={'textAlign': 'center'} ) ,

        dash_table.DataTable(
            id='tabelaTotal',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[1].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[1].to_dict('records'),
            style_cell={'textAlign': 'center'}  )



    ], className='row')
    
   
  ],className='ten columns offset-by-one')

)


#
##
# Callbacks
##
#
#neste callback utilizaremos como Output o Graph "meu-grafico-aqui"
#como Input recebemos o valor ativo no menu Dropdown (value)
@app.callback( Output('meu-grafico-aqui','figure'), [Input('uf-dropdown','value')])
#Após o callback, teremos a função que fará o update no output de acordo com o valor (value) recebido (sacou?!?!)
def update_output(value):

    dadosEstado=retornaListaEstado(value,nomeMeses,ICMS,compilado)

    graficoICMS = make_subplots(specs=[[{"secondary_y": True}]])

    graficoICMS.add_trace(
        go.Bar(x=nomeMeses, y=dadosEstado[5], name="Diferencial Absoluto"),
        secondary_y=False,
    )
    # adicionando as series
    graficoICMS.add_trace(
        go.Scatter(x=nomeMeses, y=dadosEstado[6], name="Diferencial Percentual"),
        secondary_y=True,
    )
    # Add figure title
    graficoICMS.update_layout(
        title_text="Arrecadação Acumulada de ICMS - 2020 vs. 2019",
        legend_orientation="h"
    )
  
    # Set y-axes titles
    graficoICMS.update_yaxes(title_text="Diferença Relativa, em %", secondary_y=True)
    graficoICMS.update_yaxes(title_text="Diferença Absoluta, em Reais", secondary_y=False)
    return graficoICMS

#nos proximos callbacks utilizaremos o dropdown como input para as 3 tabelas
@app.callback( Output('tabelaRecursos', 'data'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    return retonarDf(value,nomeMeses,ICMS,compilado)[0].to_dict('records')
#
@app.callback( Output('tabelaTotal', 'data'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    return retonarDf(value,nomeMeses,ICMS,compilado)[1].to_dict('records')
#
@app.callback( Output('tabelaSuficiencia', 'data'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    return retonarDf(value,nomeMeses,ICMS,compilado)[2].to_dict('records')



#não esqueça desta linha para conseguir rodar sua aplicação
if __name__ == '__main__':
   app.run_server(debug=True)