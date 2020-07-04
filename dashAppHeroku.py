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
import dash_bootstrap_components as dbc #documentaçao em https://dash-bootstrap-components.opensource.faculty.ai/


 
######
###### capturando os dados
######

enderecoAlterna="dados.xlsx"
compilado=pd.read_excel(enderecoAlterna,sheet_name="Compilado",index_col=0)
ICMS=pd.read_excel(enderecoAlterna,sheet_name="ICMS",index_col=0)
nomeMeses=["janeiro","fevereiro","março","abril","maio"]
beginner='TD' #estado que é plotado na abertura, se alterar aqui, alterar dentro de listaPorEstado
benchSuficiencia=1.0 #barra de suficiência que sera benchmark para os indices que serao traçados
textoArrecada='Não perdeu arrecadação.' 

#todosNomes é uma lista de lista, cada sublista conterá em 0 o label e em 1 o value
#para ser usado no dropdown da página
todosNomes=[]
for i in range(len(compilado.index.values)):
    todosNomes.append([compilado['UF_nome'][i],compilado.index.values[i]])

def truncar(numero,ncasas):
  return int(numero * (10**ncasas)) / (10**ncasas)

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
  #8 - nome do estado

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

def retornaSuficiencia(EstadoAlvo,nomeMeses,ICMS,compilado):
  dadosEstado=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado)
  if dadosEstado[5][-1] >= 0 :
    testeSuficiencia = textoArrecada 
  else:
    testeSuficiencia=-1*sum(dadosEstado[7])/dadosEstado[5][-1]

  
  return testeSuficiencia


def retonarDf(EstadoAlvo,nomeMeses,ICMS,compilado):
  #vai retornar uma lista de dataFrames, com a seguinte estrutura
  # 0 - dataframe contendo os dados de recursos recebidos, MP e LC 173 e de suspensão de dívida
  # 1 - dataframe contendo os dados de total e de icms perdido até agora
  # 2 - dataframe contendo o índice de suficiencia
  # 3 - dataframe empilhando soma do suporte, perda de arrecadacao e perda de suficiencia
  # 4 - dataframe linha contendo Recursos Detalhados, Soma do Suporte, Perda de ICMS
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
  label='Suficiência do Suporte (1)'
  if dadosEstado[5][-1] >= 0 :
    dataF = pd.DataFrame({label: [textoArrecada]}, index=[EstadoAlvo])  
  else:
    dataF = pd.DataFrame({label: [percentualToString(retornaSuficiencia(EstadoAlvo,nomeMeses,ICMS,compilado))]}, index=[EstadoAlvo])
  
  listadeDF.append(dataF)


  dataTab=[]
  nomeColunas=[compilado.loc[EstadoAlvo,'UF_nome'],'Valores']
  dataTab.append(['Recursos Recebidos',sum(dadosEstado[7])])
  dataTab.append(['ICMS Perdido',dadosEstado[5][-1]])
  dataTab.append(['Suficiência do Suporte',retornaSuficiencia(EstadoAlvo,nomeMeses,ICMS,compilado)])
  listadeDF.append(pd.DataFrame(dataTab,columns=nomeColunas))

  # quinto item
  dataF = pd.DataFrame({'Recursos MP938': [numToMString(dadosEstado[7][0])],
                   'Recursos LC 173': [numToMString(dadosEstado[7][1])],
                   'Suspensão de Dívida LC173 (2)': [numToMString(dadosEstado[7][2])],
                   'Total do Suporte':[numToMString(sum(dadosEstado[7]))],
                   'ICMS Perdido':[numToMString(dadosEstado[5][-1])]}, index=[EstadoAlvo])
  listadeDF.append(dataF)

  return listadeDF

def listaPorEstado(nomeMeses,ICMS,compilado,todosNomes):
  #em 0, o eixo x
  eixoX=[] #lista que sera retornada com os nomes por extenso dos estados
  #em 1, o primeiro eixo y (Suporte)
  eixoySuporte=[]
  #em 2, o total do suporte
  eixoyArrecad=[]
  for item in todosNomes:
    if item[1] != beginner:
      eixoX.append(item[0])
      eixoySuporte.append(sum(retornaListaEstado(item[1],nomeMeses,ICMS,compilado)[7]))
      eixoyArrecad.append(-1*retornaListaEstado(item[1],nomeMeses,ICMS,compilado)[5][-1])
  return [eixoX,eixoySuporte,eixoyArrecad]

def percentualToString(numero):
#usei para truncar os números
#funcao decimal tmb disponivel, mas nao quis importa uma biblioteca so para isso
  num=str(truncar(100*numero,1))
  perc=" %"
  return str(num+perc)

def numToMString(numero):
#converte um float para uma string em milhoes com separador e cifra
  numero=truncar(numero/(10**6),1)
  numString=f"{numero:,}" #converte para string com separadores
  numString=numString.replace('.','&')
  numString=numString.replace(',','.')
  numString=numString.replace('&',',')
  cifra='R$ '
  milhoes=' milhões'
  return (cifra+numString+milhoes)



####
####
#### SITE
####
####


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server=app.server #li em um tutorial q era necessario p o heroku
app.title='LC 173 Monitora'
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'}) #Bootstrap CSS

obs1="(1) Suficência do suporte é o total do suporte recebido / perda de ICMS de 2020 em relação à 2019"
obs2="(2) Suspensão de dívida = União + Instituições Financeiras Públicas"
obs3="(3) Em verde os Estados que não apresentaram perda de arrecadação"
#
# estilos para o layout
#
tabelaTop = { 'align-items': 'center' }
tabelasEstilo = { 'vertical-align': 'cmiddle'}

#
#
#o layout vai conter todos os componentes do site, html e componentes dash
#os componentes foram construídos usando a documentação da biblioteca dash-bootstrap-components
#
app.layout = html.Div([

  #primeira linha contendo o head
  dbc.Row([
    #head
    dbc.Col(dbc.Jumbotron([
        html.H1("Suporte aos Entes Federativos", className="display-3"),
        html.P(
            "Monitoramento dos recursos de suporte aos Entes Federativos em meio à pandemia do COVID-19",
            className="lead",
        ),
    ] ), width={"size": 12, "offset": 0}),
    ]),
  #segunda linha contendodo o dropdown
  dbc.Row(

    #dropdown
    dbc.Col(
      #menu dropdown com a id para ser acessado via callback e a lista de opções geradas a partir do dataframe
      dcc.Dropdown(
          id='uf-dropdown',
          options=[{'label':i[0],'value':i[1]} for i in todosNomes],
          value=beginner,
          clearable=False) , width={"size": 10, "offset": 1}) 
    ),
  #terceira linha contendo o gráfico e a tabela
  dbc.Row([
    #gráfico
    dbc.Col(
      html.Div([
         dcc.Graph(id='meu-grafico-aqui')],className= 'eight columns'),width={"size": 7, "offset": 1}),
    #tabela 1
    dbc.Col(      
      html.Div([
          dash_table.DataTable(
            id='tabelaSuficiencia',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[2].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[2].to_dict('records'),
            style_cell={'textAlign': 'center'})
              ],),width={"size": 3, "offset": 0}),

    ], align='center'),
  #quarta linha contendo a tabela detalhada
  dbc.Row(
    dbc.Col(
    html.Div([

        dash_table.DataTable(
            id='tabelaRecursos',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[4].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[4].to_dict('records'),
            style_cell={'textAlign': 'center'} ) ,
    ], ),width={"size": 10, "offset": 1})
        ), #fim da quarta row

  dbc.Row(
    dbc.Col(
      html.Div([
          dcc.Graph(id='graficoEstados'),
        ]), width={"size": 10, "offset": 1})
  ), #fim da quinta row

  dbc.Row(
    dbc.Col(
      html.Div([
          dcc.Graph(id='graficoISuficiencia'),
        ]), width={"size": 10, "offset": 1})
  ), #fim da sexta row

  dbc.Row(
    dbc.Col(
      html.Div([
        dbc.Card(
            dbc.CardBody("Observações: " + obs1 + " " + obs2 + " " + obs3),
            className="mb-3",
        ),
    ]), width={"size": 10, "offset": 1})
    ), #fim da setima row



  ],className='ten columns offset-by-one') #fim do app.layout e do Div master

#],className='ten columns offset-by-one)'''

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
#
@app.callback( Output('tabelaSuficiencia', 'data'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    return retonarDf(value,nomeMeses,ICMS,compilado)[2].to_dict('records')
#
@app.callback( Output('tabelaRecursos', 'data'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    return retonarDf(value,nomeMeses,ICMS,compilado)[4].to_dict('records')

@app.callback( Output('graficoEstados','figure'), [Input('uf-dropdown','value')])
#Após o callback, teremos a função que fará o update no output de acordo com o valor (value) recebido (sacou?!?!)
def update_output(value):

    eixos=listaPorEstado(nomeMeses,ICMS,compilado,todosNomes)

    graficoEstados=go.Figure()

    #criando lista para colorir de maneira personalizada os dados de arrecadacao
    coresBarra=[]
    for valor in eixos[2]:
      if valor>=0:
        #cor quando perdeu arrecadacao
        coresBarra.append('rgb(196, 22, 22)')
      else:
        #cor quando ganhou arrecadacao
        coresBarra.append('rgb(6, 156, 61)')
    #
    graficoEstados.add_trace(go.Bar(x=eixos[0],y=eixos[1]
      ,name='Suporte Financeiro Recebido',marker_color='rgb(55, 83, 109)'))
    graficoEstados.add_trace(go.Bar(x=eixos[0],y=eixos[2]
      ,name='Perda de Arrecadação 2020 vs 2019 (3)',marker_color=coresBarra))

    graficoEstados.update_layout(
      title='Perda de Arrecadação vs Suporte Recebido - por Estados',
      xaxis_tickfont_size=8,
      yaxis=dict(
          title='em Reais',
          titlefont_size=16,
          tickfont_size=14,
      ),
      legend=dict(
        x=0,
        y=1.0,
        bgcolor='rgba(255, 255, 255, 0)',
        bordercolor='rgba(255, 255, 255, 0)',
        orientation='h'
      ),
      barmode='group',
      bargap=0.15, # gap between bars of adjacent location coordinates.
      bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    return graficoEstados

@app.callback( Output('graficoISuficiencia','figure'), [Input('uf-dropdown','value')])
#Após o callback, teremos a função que fará o update no output de acordo com o valor (value) recebido (sacou?!?!)
def update_output(value):

  indicesSuficiencia=[] #lista que vai armazenar os indices de suficiencia de todos os estados
  eixoxSuf=[]
  for item in todosNomes:
    if item[1]!= beginner:
      eixoxSuf.append(item[0])
      if retornaSuficiencia(item[1],nomeMeses,ICMS,compilado) != textoArrecada:
        indicesSuficiencia.append(100*retornaSuficiencia(item[1],nomeMeses,ICMS,compilado))
      else:
        indicesSuficiencia.append(0)

  graficoSuf=go.Figure()

  #criando lista para colorir de maneira personalizada os dados de arrecadacao
  coresBarra=[]
  for valor in indicesSuficiencia:
    if valor>=100*benchSuficiencia:
      #cor para valor maior que o benchmark de suficiencia
      coresBarra.append('rgb(55, 83, 109)')
    else:
      coresBarra.append('rgb(196, 22, 22)')
  #
  graficoSuf.add_trace(go.Bar(x=eixoxSuf,y=indicesSuficiencia
    ,name='Suporte Financeiro Recebido',marker_color=coresBarra))

  graficoSuf.add_shape(
    type="line",
    x0=eixoxSuf[0],
    y0=100*benchSuficiencia,
    x1=eixoxSuf[-1],
    y1=100*benchSuficiencia,
        )
  graficoSuf.update_shapes(dict(
    xref="x",
    yref="y",
    opacity=0.5,
    line=dict(
        color="Crimson",
        width=2,
        )))
  graficoSuf.update_layout(
    title='Índices de Suficiência - por Estados (Linha Horizontal em 100%)',
    xaxis_tickfont_size=8,
    yaxis=dict(
        title='em %',
        titlefont_size=16,
        tickfont_size=14,
    ),
    legend=dict(
      x=0,
      y=1.0,
      bgcolor='rgba(255, 255, 255, 0)',
      bordercolor='rgba(255, 255, 255, 0)',
      orientation='h'
    ),
    barmode='group',
    bargap=0.15, # gap between bars of adjacent location coordinates.
    bargroupgap=0.1 # gap between bars of the same location coordinate.
  )
  return graficoSuf

#não esqueça desta linha para conseguir rodar sua aplicação
if __name__ == '__main__':
   app.run_server(debug=True)