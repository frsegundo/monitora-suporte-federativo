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

enderecoAlterna="dadosTeste.xlsx"
compilado=pd.read_excel(enderecoAlterna,sheet_name="Compilado",index_col=0)
ICMS=pd.read_excel(enderecoAlterna,sheet_name="ICMS",index_col=0)
IPVA=pd.read_excel(enderecoAlterna,sheet_name="IPVA",index_col=0)
Rec173=pd.read_excel(enderecoAlterna,sheet_name="Recursos173",index_col=0)
Sus173=pd.read_excel(enderecoAlterna,sheet_name="Suspensao173",index_col=0)
nomeMeses=["janeiro","fevereiro","março","abril","maio","junho"]
beginner='TD' #estado que é plotado na abertura, se alterar aqui, alterar dentro de listaPorEstado
benchSuficiencia=1.0 #barra de suficiência que sera benchmark para os indices que serao traçados
textoArrecada='Não perdeu arrecadação.'
labelIPVAICMS='ICMS + IPVA Perdido'

cotaparteICMS=0.75
cotaparteIPVA=0.5
#todosNomes é uma lista de lista, cada sublista conterá em 0 o label e em 1 o value
#para ser usado no dropdown da página
todosNomes=[]
for i in range(len(compilado.index.values)):
    todosNomes.append([compilado['UF_nome'][i],compilado.index.values[i]])

def truncar(numero,ncasas):
  return int(numero * (10**ncasas)) / (10**ncasas)

def retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA):

  #Criar uma lista para cada estado com os seguintes dados
  #0 - Nome dos Meses 
  #1 - ICMS + IPVA de 2019 
  #2 - ICMS + IPVA de 2020 
  #3 - ICMS + IPVA acumulado 2019 
  #4 - ICMS + IPVA acumulado 2020 
  #5 - diferencial absoluto dos ICMS's acumulados 
  #6 - diferencial percentual dos ICMS's acumulados 
  #7 - lista contendo as ajudas totais decorrentes de LC173_Recursos, LC173_Suspensão e MP938
  #8 - True se estiver atualizado, false se estiver desatualizado
  #9 - Lista com os diferenciais %, mês contra mês


  dadosEstado=[]
  NMeses=len(nomeMeses)

  dadosEstado.append(nomeMeses)

  selecao2019=list(range(0,NMeses))
  selecao2020=list(range(NMeses,NMeses*2))
  selecaoAjudas=list(range(1,4))

  #testando se esta atualizado ou não
  #no início do mes, apenas alguns estados atualizam os valores
  #o codigo tem sempre que estar pronto para tratar dados até o mes n em conjunto com dados ate o mes (n-1)
  #a premissa é que se não tem o mês n em 2019, tmb não o terá em 2020
  flagAtualizado=True
  listaTeste=ICMS.loc[EstadoAlvo].iloc[selecao2019].tolist() #os valores de icms de 2019
  #o que vai mudar são os ranges de selecao, um para cada caso (atualizadou ou nao atualizado)
  if listaTeste[-1]!=listaTeste[-1]: #só vai ser true se for NaN
    flagAtualizado=False #vai dar false se não tiver dados para o último mês
    selecao2019=list(range(0,NMeses-1)) 
    selecao2020=list(range(NMeses,NMeses*2-1))
    NMeses=NMeses-1

  #somando as listas ICMS e IPVA, elemento a elemento
  ICMS19=ICMS.loc[EstadoAlvo].iloc[selecao2019].tolist()
  ICMS19 = [x * cotaparteICMS for x in ICMS19]
  ICMS20=ICMS.loc[EstadoAlvo].iloc[selecao2020].tolist()
  ICMS20 = [x * cotaparteICMS for x in ICMS20]
  IPVA19=IPVA.loc[EstadoAlvo].iloc[selecao2019].tolist()
  IPVA19 = [x * cotaparteIPVA for x in IPVA19]
  IPVA20=IPVA.loc[EstadoAlvo].iloc[selecao2020].tolist()
  IPVA20 = [x * cotaparteIPVA for x in IPVA20]
  dadosEstado.append([sum(x) for x in zip(ICMS19, IPVA19)]) #adicionando os valores de ICMS + IPVA de 2019
  dadosEstado.append([sum(x) for x in zip(ICMS20, IPVA20)]) #adicionando os valores de ICMS + IPVA de 2020

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

  #adicionando o teste para saber se está atualizado
  dadosEstado.append(flagAtualizado)

  #adicionando os diferenciais % mes contra mes
  dadosEstado.append([(i20/i19-1) for i19,i20 in zip(ICMS19, ICMS20)]) #adicionando os valores de ICMS + IPVA de 2019

  return dadosEstado

def retornaSuficiencia(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA):
  #esse indice é o total do suporte recebido sobre o delta da arrecadacao acumulada
  dadosEstado=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA)
  if dadosEstado[5][-1] >= 0 :
    testeSuficiencia = textoArrecada 
  else:
    testeSuficiencia=-1*(dadosEstado[7][1]+dadosEstado[7][2])/dadosEstado[5][-1]

  
  return testeSuficiencia

def retornaSufNew(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA):
  #esse indice é o acumulado de 2020 + suporte dividido pelo acumulado de 2019
  dadosEstado=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA)
  acumulado2020=dadosEstado[4][-1]
  acumulado2019=dadosEstado[3][-1]
  suporte173=dadosEstado[7][1]+dadosEstado[7][2]
  return (acumulado2020+suporte173)/acumulado2019


def retonarDf(EstadoAlvo,nomeMeses,ICMS,compilado):
  #vai retornar uma lista de dataFrames, com a seguinte estrutura
  # 0 - dataframe contendo os dados de recursos recebidos, MP e LC 173 e de suspensão de dívida
  # 1 - dataframe contendo os dados de total e de icms perdido até agora
  # 2 - dataframe contendo o índice de suficiencia
  # 3 - dataframe empilhando soma do suporte, perda de arrecadacao e perda de suficiencia
  # 4 - dataframe linha contendo Recursos Detalhados, Soma do Suporte, Perda de ICMS + IPVA
  listadeDF=[]
  #primeiro item
  dadosEstado=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA)
  dataF = pd.DataFrame({'Recursos MP938': [dadosEstado[7][0]],
                   'Recursos LC 173': [dadosEstado[7][1]],
                   'Suspensão de Dívida LC173': [dadosEstado[7][2]]}, index=[EstadoAlvo])
  listadeDF.append(dataF)
  #segundo item
  dataF = pd.DataFrame({'Suporte Financeiro': [sum(dadosEstado[7])],
                   labelIPVAICMS: [dadosEstado[5][-1]]}, index=[EstadoAlvo])
  listadeDF.append(dataF)
  #terceiro item
  label='Suficiência do Suporte (1)'
  dataF = pd.DataFrame({label: [percentualToString(retornaSufNew(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA))]}, index=[EstadoAlvo])
  
  listadeDF.append(dataF)


  dataTab=[]
  nomeColunas=[compilado.loc[EstadoAlvo,'UF_nome'],'Valores']
  dataTab.append(['Recursos Recebidos',sum(dadosEstado[7])])
  dataTab.append([labelIPVAICMS,dadosEstado[5][-1]])
  dataTab.append(['Suficiência do Suporte',retornaSuficiencia(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA)])
  listadeDF.append(pd.DataFrame(dataTab,columns=nomeColunas))

  # quinto item
  dataF = pd.DataFrame({'Recursos MP938': [numToMString(dadosEstado[7][0])],
                   'Recursos LC 173': [numToMString(dadosEstado[7][1])],
                   'Suspensão de Dívida LC173 (2)': [numToMString(dadosEstado[7][2])],
                   'Total do Suporte':[numToMString(sum(dadosEstado[7]))],
                   #multipliquei o próximo por -1 para manter o padrão de perda positiva, ganho negativo
                   labelIPVAICMS:[numToMString(-1*dadosEstado[5][-1])]}, index=[EstadoAlvo])
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
      dadosEstado=retornaListaEstado(item[1],nomeMeses,ICMS,compilado,IPVA)
      eixoX.append(item[0])
      eixoySuporte.append(dadosEstado[7][1]+dadosEstado[7][2])
      eixoyArrecad.append(-1*dadosEstado[5][-1])
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

def ICMSatualizado(nomeMeses,ICMS,compilado):
  #retorna false se tiver pelo menos um estado desatualizado, e o número de estados desatualizados
  teste=True
  contador=0
  for item in todosNomes:
    if item[1] != beginner:
      if retornaListaEstado(item[1],nomeMeses,ICMS,compilado,IPVA)[8]==False:
        teste=False
        contador +=1
  return [teste,contador]

def dadosMesMes(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA,Rec173,Sus173):
  #retorna os eixos para o gráfico mês a mês
  #para cada mês duas barras, uma de 2019 e outra de 2020
  #Arrecadação vs Arrecadação + 173
  #item 0 de eixos - nomes dos eixos de x
  #item 1 de eixos - barras de 2019
  #item 2 de eixos - barras de 2020, arrecadacao
  #item 3 de eixos - Recursos 173 + Suspensao, mes a mes
  dadosTemp=retornaListaEstado(EstadoAlvo,nomeMeses,ICMS,compilado,IPVA)
  mm=[]
  if dadosTemp[8]:
    rangeSelecao=list(range(0,len(nomeMeses)))
    mm.append(nomeMeses)
  else:
    rangeSelecao=list(range(0,len(nomeMeses)-1))
    mm.append(nomeMeses[:-1]) #passa todos os meses, exceto o último

  mm.append(dadosTemp[1]) #arrecadacao 2019 mes a mes
  mm.append(dadosTemp[2]) #arrecadacao 2020 mes a mes

  Rec173mm=Rec173.loc[EstadoAlvo].iloc[rangeSelecao].tolist()
  Sus173mm=Sus173.loc[EstadoAlvo].iloc[rangeSelecao].tolist()

  mm.append([sum(x) for x in zip(Rec173mm, Sus173mm)]) #suporte 173 mes a mes


  return mm




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

obs1="(1) Suficência do suporte é o [Total do suporte recebido nos termos da 173 + Arrecadacao (IPVA+ICMS) acumulada de 2020] / Arrecadacao (IPVA+ICMS) acumulada de 2019"
obs2="(2) Suspensão de dívida com a União"
obs3="(3) Em verde os Estados que não apresentaram perda de arrecadação"

#alerta de ICMS desatualizado
corAlerta="white"
textoAlerta=""
alertaUpToDate=ICMSatualizado(nomeMeses,ICMS,compilado)
if alertaUpToDate[0]==False:
  corAlerta="warning"
  if alertaUpToDate[1]>1:
    textoAlerta=str(alertaUpToDate[1]) + " Estados ainda não atualizaram os dados de arrecadação para " + nomeMeses[-1]
  else:
    textoAlerta="1 Estado ainda não atualizou os dados de arrecadação para " + nomeMeses[-1]
#cor do texto de perda de arrecadacao
corArrecad='black'
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
          html.Div([
            dash_table.DataTable(
            id='tabelaSuficiencia',
            columns=[{"name": i, "id": i} for i in retonarDf(beginner,nomeMeses,ICMS,compilado)[2].columns],
            data=retonarDf(beginner,nomeMeses,ICMS,compilado)[2].to_dict('records'),
            style_cell={'textAlign': 'center'}),]),
          #alerta nos casos em que há estados com numeros de ICMS ainda desatualizados
          html.Div([ dbc.Alert(textoAlerta, color=corAlerta,style={ 'margin-top': '5%'},dismissable=not alertaUpToDate[0])]),    
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
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
            {'if': {'column_id': labelIPVAICMS},
             'color': corArrecad,
             'fontWeight': 'bold'},] 
        ) ,

    ], ),width={"size": 10, "offset": 1})
        ), #fim da quarta row


  dbc.Row(
    dbc.Col(
      html.Div([
          dcc.Graph(id='graficoMM'),
        ]), width={"size": 10, "offset": 1})
  ), #fim da sexta row

  dbc.Row(
    dbc.Col(
      html.Div([
          dcc.Graph(id='graficoISuficiencia'),
        ]), width={"size": 10, "offset": 1})
  ), #fim da sétima row

  dbc.Row(
    dbc.Col(
      html.Div([
          dcc.Graph(id='graficoEstados'),
        ]), width={"size": 10, "offset": 1})
  ), #fim da row

   dbc.Row(
      dbc.Col(
        dbc.CardDeck([
          dbc.Card(
            dbc.CardBody([
              html.H5("MP 938", className="card-title"),
              html.P(
                  "Recomposição, por 4 meses, dos repasses de FPM e de FPE ao nível do que foi realizado em 2019. "
                  "Atualizado com os 4 pagamentos já realizados. Sem pagamentos pendentes, medida de apoio encerada."
                  ),]), style={"width": "18rem"},),
          dbc.Card(
            dbc.CardBody([
              html.H5("Recursos LC 173", className="card-title"),
              html.P(
                  "Repasse de recursos definidos no Art. 5 da Lei Complementar 173, de 2020.  "
                  "Dados atualizados com as parcelas de 09jun e 13jul. Duas parcelas ainda pendentes."
                  ),]), style={"width": "18rem"},),
          dbc.Card(
            dbc.CardBody([
              html.H5("Suspensão de Dívida LC 173", className="card-title"),
              html.P(
                  "Dados atualizados de acordo com dados de suspensão de dívida dos Estados com União e com Instituições Financeiras Públicas.  "
                  "Dívidas já suspensas anteriormente à pandemia não são contabilizadas."
                  ),]), style={"width": "18rem"},),
          ]) #fim do CardDeck
        , width={"size": 10, "offset": 1},style={ 'margin-top': '0%'})
    ), #fim da quinta row

    dbc.Row(
      dbc.Col(
      html.Div([
        dbc.Card(
            dbc.CardBody("Observações: " + obs1 + " " + obs2 + " " + obs3),
            className="mb-3",
        ),
    ]), width={"size": 10, "offset": 1},style={ 'margin-top': '1%'})
    ), #fim da oitava row


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

    dadosEstado=retornaListaEstado(value,nomeMeses,ICMS,compilado,IPVA)

    graficoICMS = make_subplots(specs=[[{"secondary_y": True}]])

    graficoICMS.add_trace(
        go.Bar(x=nomeMeses, y=dadosEstado[9], name="Diferencial Percentual Mês a Mês"),
        secondary_y=False,
    )
    # adicionando as series
    graficoICMS.add_trace(
        go.Scatter(x=nomeMeses, y=dadosEstado[6], name="Diferencial Percentual do Acumulado"),
        secondary_y=True,
    )
    # Add figure title
    graficoICMS.update_layout(
        title_text="Arrecadação ICMS + IPCA -> 2020 vs. 2019",
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

@app.callback( Output('tabelaRecursos', 'style_data_conditional'),[Input('uf-dropdown', 'value')])
def update_selected_row_indices(value):
    if retornaSuficiencia(value,nomeMeses,ICMS,compilado,IPVA) != textoArrecada:
        corArrecad='tomato' #quando perde arrecadação
    else:
        corArrecad='green'  # quando ganha arrecadação
    estilo=[
            {'if': {'column_id': labelIPVAICMS},
             'color': corArrecad,
             'fontWeight': 'bold'}]
    return estilo

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
      ,name='Suporte LC 173 - Repasse de Recursos + Suspensão de Dívida',marker_color='rgb(55, 83, 109)'))
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

@app.callback( Output('graficoMM','figure'), [Input('uf-dropdown','value')])
#Após o callback, teremos a função que fará o update no output de acordo com o valor (value) recebido
def update_output(value):

    eixosMM=dadosMesMes(value,nomeMeses,ICMS,compilado,IPVA,Rec173,Sus173) #retorna os eixos já prontos

    tempEmpilhado=[sum(x) for x in zip(eixosMM[2], eixosMM[3])]

    graficoMesMes=go.Figure(
      #inicio graficoMesMes
      data=[
        go.Bar(name="Arrecadação 2019",x=eixosMM[0],y=eixosMM[1],offsetgroup=0,marker_color='rgb(55, 83, 109)'),
        go.Bar(name="Arrecadação 2020 + Suporte LC 173",x=eixosMM[0],y=tempEmpilhado,offsetgroup=1,marker_color='rgb(110, 80, 10)'),
        go.Bar(name="Suporte LC 173",x=eixosMM[0],y=eixosMM[3],offsetgroup=1,marker_color='rgb(229, 165, 17)')
      ],
      layout=go.Layout(title='Arrecadação (ICMS + IPVA) e Suporte (LC 173) - Mês a Mês',yaxis_title='em R$',legend_orientation="h")
      #fim graficoMesMes
      )

    return graficoMesMes

@app.callback( Output('graficoISuficiencia','figure'), [Input('uf-dropdown','value')])
#Após o callback, teremos a função que fará o update no output de acordo com o valor (value) recebido (sacou?!?!)
def update_output(value):

  indicesSuficiencia=[] #lista que vai armazenar os indices de suficiencia de todos os estados
  eixoxSuf=[]
  for item in todosNomes:
    if item[1]!= beginner:
      eixoxSuf.append(item[0])
      indicesSuficiencia.append(100*retornaSufNew(item[1],nomeMeses,ICMS,compilado,IPVA))

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
  graficoSuf.update_yaxes(range=[75, 200]) # eixo y da figura customizado manualmente
  return graficoSuf

#não esqueça desta linha para conseguir rodar sua aplicação
if __name__ == '__main__':
   app.run_server(debug=True)