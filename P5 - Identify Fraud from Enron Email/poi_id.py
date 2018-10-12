#!/usr/bin/python

import sys
import pickle
import pandas
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data, test_classifier

### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)

### Explore Data
# import dicitonary into a dataframe and change datatypes to numbers
df = pandas.DataFrame.from_dict(data_dict,orient='index')
cols = df.columns[df.dtypes.eq('object')].drop('email_address')
df[cols] = df[cols].apply(pandas.to_numeric, errors='coerce')
# find the percentage items in a column that are not null
print 'Percentage of Non NaN'
print 1-(df.isnull().sum()/len(df))
print ''
# find the percentage of items in a row that are null
print "Top 5 amount NaN's in a given row"
print df.isnull().sum(axis=1).sort_values(ascending=False).head()
print ''
# look at Lockhart who has all fields null except POI
print df.loc['LOCKHART EUGENE E']
print ''
#remove lockhart
df = df.drop(['LOCKHART EUGENE E'])
# look at Travel Agency in the Park
print df.loc['THE TRAVEL AGENCY IN THE PARK']
print ''
#remove travel agency
df = df.drop(['THE TRAVEL AGENCY IN THE PARK'])
# look at a histogram of salary
df.hist(column='salary')
plt.savefig('fig.png')
# look at outlier salary
print df['salary'].sort_values(ascending=False).head()
print ''
print df.loc['TOTAL']
print ''
# remove outlier salary and look at histogram again
df = df.drop(['TOTAL'])
df.hist(column='salary')
plt.savefig('fig2.png')


### Remove outliers
data_dict.pop('LOCKHART EUGENE E')
data_dict.pop('THE TRAVEL AGENCY IN THE PARK')
data_dict.pop('TOTAL')

### Create new features
def computeFraction( poi_messages, all_messages ):
    """ given a number messages to/from POI (numerator) 
        and number of all messages to/from a person (denominator),
        return the fraction of messages to/from that person
        that are from/to a POI
   """
    fraction = 0.
    if poi_messages == 'NaN' or all_messages == 'NaN':
        fraction = 0.
    else:
        fraction = float(poi_messages)/float(all_messages)
    return fraction

for name in data_dict:
    from_poi_to_this_person = data_dict[name]["from_poi_to_this_person"]
    to_messages = data_dict[name]["to_messages"]
    fraction_from_poi = computeFraction(from_poi_to_this_person, to_messages)
    
    from_this_person_to_poi = data_dict[name]["from_this_person_to_poi"]
    from_messages = data_dict[name]["from_messages"]
    fraction_to_poi = computeFraction(from_this_person_to_poi, from_messages)
    
    data_dict[name]["fraction_from_poi"] = fraction_from_poi
    data_dict[name]["fraction_to_poi"] = fraction_to_poi
    

### Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = ['poi','salary', 'deferral_payments', 'total_payments',\
'loan_advances', 'bonus', 'restricted_stock_deferred', 'deferred_income',\
'total_stock_value', 'expenses', 'exercised_stock_options', 'other',\
'long_term_incentive', 'restricted_stock', 'director_fees', 'to_messages',\
'from_poi_to_this_person', 'from_messages', 'from_this_person_to_poi',\
'shared_receipt_with_poi','fraction_from_poi','fraction_to_poi']

### Store to my_dataset for easy export below.
my_dataset = data_dict

### Extract features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)

### K Best feature selection
selector = SelectKBest(k=10)
selector = selector.fit(features,labels)
scores = pandas.DataFrame(columns=['score'])
x = 1
for i in features_list[1:]:
    scores.loc[features_list[x]] = selector.scores_[x-1]
    x += 1
print scores.sort_values('score',ascending=False)
#features = selector.transform(features)

cv = StratifiedShuffleSplit(n_splits=10, test_size=0.2, random_state=42)

### Naive Bays Pipeline and Test
pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('selector', SelectKBest()),
        ('classifier', GaussianNB())
    ])
param_grid = {
    'scaler' : [StandardScaler(), None],
    'selector__k': [5, 10, 15, 'all']
}
clf = GridSearchCV(pipe, param_grid, scoring='f1', cv=cv).fit(features,labels)
print clf.best_params_
clf = clf.best_estimator_
test_classifier(clf, my_dataset, features_list)

# Decision Tree Pipeline and Test
pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('selector', SelectKBest()),
        ('classifier', DecisionTreeClassifier())
    ])
param_grid = {
    'scaler' : [StandardScaler(), None],
    'selector__k': [5, 10, 15, 'all'],
    'classifier__criterion' : ['gini'],
    'classifier__splitter' :  ['best', 'random'],
    'classifier__class_weight' : ['balanced'],
    'classifier__max_depth' : [18, 20, 22, None],
    'classifier__min_samples_leaf': [1, 2, 3],
    'classifier__max_leaf_nodes': [7, 8, 9]
}
clf = GridSearchCV(pipe, param_grid, scoring='f1', cv=cv).fit(features,labels)
print clf.best_params_
clf = clf.best_estimator_
test_classifier(clf, my_dataset, features_list)

# SVC Pipeline and Test
pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('selector', SelectKBest()),
        ('classifier', SVC())
    ])
param_grid = {
    'scaler' : [StandardScaler()],
    'selector__k' : [5, 10, 15, 'all'],
    'classifier__gamma' : [0.001, 0.01, 0.1, 1],
    'classifier__C' : [0.001, 0.01, 0.1, 1, 10, 100],
    'classifier__kernel' : ['rbf','sigmoid'],
    'classifier__class_weight' : ['balanced', None]
}
clf = GridSearchCV(pipe, param_grid, scoring='f1', cv=cv).fit(features,labels)
print clf.best_params_
clf = clf.best_estimator_
test_classifier(clf, my_dataset, features_list)

### Dump your classifier, dataset, and features_list so anyone can
### check your results. 
dump_classifier_and_data(clf, my_dataset, features_list)