# Nazwy  zadań
jobName='MODEL-CHECK'
taskName='OPTIMIZATION-TASK'
processName='TEST-OPT-2D-MODEL'
optJobName='{}-JOB'.format(processName)

# Rozmiar elementu skończonego
meshSize=5.0

# Geometria
witdth=float(1200) ## Długość w mm
height=float(200) ## Wysokość w mm
LS=float(40) ## Length of support in mm

# Ograniczenia geometryczne
rmin=float(1.5*meshSize)
minSizeTop=float(meshSize)
planarSym=True
demold=False

# Właściwości materiałowe
E=float(210000) ## Moduł Younga N/mm2
p=float(0.3) ## Współczynnik Poissona

# Parametry optymalizacji
VF=float(0.5) ## Objętość
operation='SUM'

# Ustawienia zadania obliczeniowego
interpolationPenalty=3.0 ## Współczynnik kary (domyślnie=3)
## Gęstość
minDens=0.001 ## Minimalna gęstość (domyślnie=0.001)
maxDens=1.0 ## Maksymalna gęstość (domyślnie=1.0)
maxDeltaDens=0.20 ## Maximum change per design cycle (default=0.25)
initialDens=VF ## Initial density (default=DEFAULT)

### Kryteria zatrzymania
conObjective=float(0.001) #Minimalna różnica między inkrementacjami
conDensity=float(0.005) #Minimalna różnica między inkrementacjami
mDC=int(1000) ## Maksymalna liczba cykli

# Ustawienia wobec komputera
numCores=int(6) #Liczba wykożystywanych rdzeni procesora
perMem=int(90) # Procentowe wykożystanie procesora

# Uruchomienie obliczeń
submitJob=False
submitOpt=False

# Zdefinowanie obciążeń

# Ustawienie obciążenia
concentrate_force=float(-500.0) ## Wartość wartość siły w N

# Importowanie bibliotek
from part import * 
from material import * 
from section import * 
from assembly import * 
from step import * 
from interaction import * 
from load import * 
from mesh import * 
from optimization import * 
from job import * 
from sketch import * 
from visualization import * 
from connectorBehavior import * 

# Ścieżka dostępu
import os
folder=os.getcwd()
pathProcess=os.path.join(folder, processName)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)

# Nazwa modelu
modelName='LC-1' ## Nie używać nazwy: Model-1

# Utworzenie nowego modelu i usunięcie Model-1
mdb.Model(modelType=STANDARD_EXPLICIT, name=modelName)
if 'Model-1' in mdb.models: del mdb.models['Model-1']

# Wyczyszczenie pamięci
mod=mdb.models[modelName]

# x,y
x=float(witdth*0.5)
y=float(height*0.5)

# Utworzenie części
mod.ConstrainedSketch(name='__profile__', sheetSize=2000.0)
## Wyczyszczenie pamięci
modske=mod.sketches['__profile__']

#*******************************************************
## Pionowa lewa
p1,p2=(-x, y),(-x, -y)
modske.Line(point1=p1, point2=p2)
## Pozioma dolna
p1,p2=p2,(x, -y)
modske.Line(point1=p1, point2=p2)

p1,p2=p2, (x,-0.5*LS)
modske.Line(point1=p1, point2=p2)

p1,p2=p2, (x,0.5*LS)
modske.Line(point1=p1, point2=p2)

# ## Pionowa prawa
# p1,p2=p2,(x, 0.0)
# modske.Line(point1=p1, point2=p2)
p1,p2=p2,(x, y)
modske.Line(point1=p1, point2=p2)
#Pozioma górna
p1,p2=p2,(-x, y)
modske.Line(point1=p1, point2=p2)
#*********************************************************

## Utworzenie części
mod.Part(dimensionality=TWO_D_PLANAR, name='PART-1', type=DEFORMABLE_BODY)
mod.parts['PART-1'].BaseShell(sketch=modske)
del modske, mod.sketches['__profile__'], p1, p2

# Przypisanie zmiennych
modpa=mod.parts['PART-1']

# Stworzenie konfiguracji: PART-1
modpa.Set(faces=modpa.faces.getSequenceFromMask(('[#1 ]', ), ), name='PART-1')

# Utworzenie materiału
mod.Material(name='STEEL')
mod.materials['STEEL'].Elastic(table=((E, p), ))

# Utworzenie sekcji
mod.HomogeneousSolidSection(material='STEEL', name='SECTION-1', thickness=None)

# Przypisanie sekcji
modpa.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE,
    region=modpa.sets['PART-1'], sectionName='SECTION-1', thicknessAssignment=FROM_SECTION)

# Przypisanie zmiennych
modra=mod.rootAssembly

# Złożenie
modra.DatumCsysByDefault(CARTESIAN)
modra.Instance(dependent=ON, name='PART-1-1', part=modpa)

# Przypisanie zmiennych
modrain=modra.instances['PART-1-1']

## Obszar projektowy
findat2=(0.0, 0.0, 0.0) # Wskazanie punktu (0,0,0)
modra.Set(faces=modrain.faces.findAt((findat2, )), name='DESIGN-AREA')
del findat2

# Zdefinowanie miejsca do którego zostaną przyłożone warunki brzegowe
edge1 = modrain.edges.findAt(((-x, 0.0, 0.0),))
modra.Set(edges=edge1, name='EDGE-BC-1')
del edge1

# Utworzenie kroku
mod.StaticStep(name='STEP-1', previous='Initial')

# Usunięcie standardowych wartości wejściowych
del mod.fieldOutputRequests['F-Output-1']
# Utworzenie nowych wartości wejściowych
mod.FieldOutputRequest(createStepName='STEP-1', name='F-Output-1',
    variables=('S', 'MISES', 'E', 'EE', 'NE', 'U', 'RF', 'P', 'COORD', 'ENER', 'ELEN', 'ELEDEN'))

## Edge for applying support 1
findat=(x, 0.0, 0.0)
modra.Set(name='EDGE-FORCE-1', edges=modrain.edges.findAt((findat, )))
# ## Edge for applying support 2
# findat=(x-0.5*LS, -y, 0.0)
# modra.Set(name='EDGE-BC-2', edges=modrain.edges.findAt((findat, )))

# Create reference point for boundary conditions
## RF-1
findat=(x, 0.0, 0.0)
modra.ReferencePoint(point=modrain.InterestingPoint(modrain.edges.findAt(findat, ), MIDDLE))
listRP=listRP=modra.referencePoints.keys()
numRP1=listRP[0]
modra.Set(name='RP-1', referencePoints=(modra.referencePoints[numRP1], ))

# Create rigid body constraints
mod.RigidBody(name='CONSTRAINT-BC-1', pinRegion=modra.sets['EDGE-FORCE-1'],
    refPointRegion=modra.sets['RP-1'])

# Przyłożenie obciążenia (siła skupiona)
region = modra.sets['RP-1']
mod.ConcentratedForce(name='Load-1', createStepName='STEP-1',
    region=region, cf2=concentrate_force, distributionType=UNIFORM, field='',
    localCsys=None)


# Ustawienie warunków brzegowych
# Utwierdzenie lewej części belki
mod.DisplacementBC(createStepName='Initial', name='BC-EDGE-BC-1', region=modra.sets['EDGE-BC-1'], u1=SET, u2=SET, ur3=SET)

# Nałożenie siatki mesh
modpa.seedPart(size=meshSize, deviationFactor=0.1, minSizeFactor=0.1)

# Generowanie siatki mesh
modpa.generateMesh(regions=(modrain, ))

# Utworzenie zadania obliczeniowego
mdb.Job(model=modelName, name=jobName, numCpus=numCores, numDomains=numCores,  memory=perMem,
    memoryUnits=PERCENTAGE)
if submitJob==True:
    mdb.jobs[jobName].submit(consistencyChecking=OFF)
    mdb.jobs[jobName].waitForCompletion()

# Optymalizacja topologiczna

# Przypisanie zmiennych
mod=mdb.models[modelName]
modra=mod.rootAssembly

# Zadanie optymalizacyjne
mod.TopologyTask(freezeBoundaryConditionRegions=ON, freezeLoadRegions=ON,
    materialInterpolationTechnique=SIMP, materialInterpolationPenalty=interpolationPenalty,
    name=taskName, region=modra.sets['DESIGN-AREA'], densityMoveLimit=maxDeltaDens,
    initialDensity=initialDens, maxDensity=maxDens, minDensity=minDens,
    objectiveFunctionDeltaStopCriteria=conObjective, elementDensityDeltaStopCriteria=conDensity)

# Przypisanie zmiennych
modopt=mod.optimizationTasks[taskName]

# Definiowanie procesu
if operation=='SUM':
    ope=SUM
if operation=='MAX':
    ope=MAXIMUM
if operation=='MIN':
    ope=MINIMUM

# Ustawienie wartości projektowych
modopt.SingleTermDesignResponse(name='D-RESP-1-STRAIN', region=MODEL, identifier='STRAIN_ENERGY',
    drivingRegion=None, operation=SUM, stepOptions=())

# Design response
# Objętość
modopt.SingleTermDesignResponse(drivingRegion=None, identifier='VOLUME', name='D-RESP-2-VOLUME',
    operation=SUM, region=MODEL, stepOptions=())

# Funkcja celu
modopt.ObjectiveFunction(name='OBJECTIVE-1-STRAIN',
    objectives=((OFF, 'D-RESP-1-STRAIN', 1.0, 0.0, ''), ))

# Ograniczenie
# Objętość
modopt.OptimizationConstraint(designResponse='D-RESP-2-VOLUME', name='CONSTRAINT-1-VOLUME',
    restrictionValue=VF, restrictionMethod=RELATIVE_LESS_THAN_EQUAL)

# Minimalna grubość elementu
minSize=2*rmin
if minSize>0:
    mod.optimizationTasks[taskName].TopologyMemberSize(minThickness=minSize,
        region=modra.sets['DESIGN-AREA'], sizeRestriction=MINIMUM, name='MIN-THICKNESS')

# Proces topologiczny
mdb.OptimizationProcess(dataSaveFrequency=OPT_DATASAVE_SPECIFY_CYCLE, saveEvery=None, saveFirst=False,
    saveInitial=True, maxDesignCycle=mDC, model=modelName, name=processName, odbMergeFrequency=2,
    prototypeJob=optJobName, task=taskName)
mdb.optimizationProcesses[processName].Job(model=modelName, name=optJobName,
    numCpus=numCores, numDomains=numCores, memory=perMem, memoryUnits=PERCENTAGE)

if submitOpt==True:
    ## Wywołanie procesu optymalizacji
    mdb.optimizationProcesses[processName].submit()
    ## Oczekiwanie na obliczenie
    mdb.optimizationProcesses[processName].waitForCompletion()
    ## Połączenie analiz
    mdb.CombineOptResults(analysisFieldVariables=ALL, models=ALL, optIter=ALL, steps=('STEP-1', ),
        optResultLocation=pathProcess)

########################################################################################################
### Koniec skryptu                                                                                   ###
########################################################################################################
print('END OF SCRIPT')

