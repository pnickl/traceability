import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn import neighbors

from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D

import pickle

n_train = 10000
n_neighbors = 5

# script for generating data
def gen_data(n_train):

    # create data as multivariate normal distribution
    mean = [1.5, 6, 32]
    cov = [[1, 0, 0], [0, 3, 0], [0, 0, 100]] #75

    L, D, T = np.random.multivariate_normal(mean, cov, n_train).T

    # delete datapoints where power (L), pressure (D) or temperature (T) are below zero
    idx = []
    for i in range(len(L)):
        if L[i] < 0 or D[i] < 0 or T[i] < 0:
            idx.append(i)
    L = np.delete(L, idx, 0)
    D = np.delete(D, idx, 0)
    T = np.delete(T, idx, 0)

    # create data array
    X = np.zeros((len(L), 3))
    for i in range(len(L)):
        X[i, 0] = L[i]
        X[i, 1] = D[i]
        X[i, 2] = T[i]

    return L, D, T, X


# assigning labels to the data (0= rework / Gutteil, 1= rework / Nachbearbeiten,2= scrap / Ausschuss)
def labels(L, D, T):
    # blur the lines between okay parts and rework parts
    p_blurring = [0.90, 0.10]
    cat = np.zeros(len(L))

    for i in range(len(L)):

        # set some parameters
        alpha_0 = 1
        factor = 0.00001

        # if Leistung is larger than 3, assigned label will be...
        if L[i] > 3:
            #... likely OK
            if L[i] < 3.5:
                prior = np.asarray(np.array(p_blurring))
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
            #... likely rework, increasing chance of scrap with large values of L
            else:
                alpha = np.abs((L[i] - 3)) * factor
                prior = np.random.dirichlet((alpha_0, alpha), 1)[0]
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
                # above 5 definite assign label scrap
                if L[i] > 5:
                    cat[i] += 1

        # if Druck is larger than 8, assign label...
        if D[i] > 8:
            # ... likely OK
            if D[i] < 8.5:
                prior = np.asarray(np.array(p_blurring))
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
            # ... likely rework, increasing chance of scrap with large absolute values of D
            else:
                alpha = np.abs((D[i] - 8)) * factor
                prior = np.random.dirichlet((alpha_0, alpha), 1)[0]
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
                # in these cases definitely assign label scrap
                if D[i] > 9 or T[i] > 50 or T[i] < 13:
                    cat[i] += 1

        # if Druck is smaller than 4, assign label...
        if D[i] < 4:
            # ... likely OK
            if D[i] > 3.5:
                prior = np.asarray(np.array(p_blurring))
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
            # ... likely rework, increasing chance of scrap with large absolute values of D
            else:
                alpha = np.abs((D[i] - 4)) * factor
                prior = np.random.dirichlet((alpha_0, alpha), 1)[0]
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
                # in these cases definitely assign label scrap
                if D[i] < 3 or T[i] < 13 or T[i] > 50:
                    cat[i] += 1

        # if Temperatur is larger than 4, assign label...
        if T[i] > 45:
            # ... likely OK
            if T[i] < 50:
                prior = np.asarray(np.array(p_blurring))
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
            # ... likely rework, increasing chance of scrap with large absolute values of T
            else:
                alpha = np.abs((T[i] - 45)) * factor
                prior = np.random.dirichlet((alpha_0, alpha), 1)[0]
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
                # in these cases definitely assign label scrap
                if T[i] > 50 or D[i] > 9:
                    cat[i] += 1

        # if Temperatur is smaller than 18, assign label...
        if T[i] < 18:
            # ... likely OK
            if T[i] > 13:
                prior = np.asarray(np.array(p_blurring))
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
            # ... likely rework, increasing chance of scrap with large absolute values of T
            else:
                alpha = np.abs((T[i] - 18)) * factor
                prior = np.random.dirichlet((alpha_0, alpha), 1)[0]
                cat[i] = np.random.multinomial(1, prior, size=1)[0][0]
                # in these cases definitely assign label scrap
                if T[i] < 13 or D[i] < 3:
                    cat[i] += 1

        # if Leistung is between 3.5 and 3: classify as rework
        if L[i] > 3 and L[i] < 3.5:
            cat[i] = 1

        # if Druck is between 9 and 2 OR Leistung larger than 3.5: classify as scrap
        if D[i] > 9 or D[i] < 2 or L[i] > 3.5:
            cat[i] = 2

        #  Define a certain area where parts are labeled as okay in any case, to make data more heterogenous
        if D[i] > 5 and D[i] < 7 and T[i] > 18 and T[i] < 45 and L[i] > 2.5 and L[i] < 6:
            if T[i] > (7.71 * L[i] - 1.28 ):
                cat[i] = 0

    return cat

# create and save plots
def plotting(n_train, n_neighbors):

    # load data
    L, D, T, X = gen_data(n_train)
    # assign category to data
    cat = labels(L, D, T)

    # shuffle and split training and test sets
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, cat, test_size=.3,
                                                        random_state=0)

    # we create an instance of Neighbours Classifier and fit the data.
    weights = 'uniform' # for weights in ['uniform', 'distance']:
    classifier = neighbors.KNeighborsClassifier(n_neighbors, weights=weights)
    clf = classifier.fit(X_train, y_train)

    # save model to binary with pickle to make prediction in plotly dash
    pickle.dump(clf, open("lackieren_knn_model_" + str(n_train) + ".sav", 'wb'))

    # plot training data with labels
    fig1 = pyplot.figure()
    ax = Axes3D(fig1)
    plt.grid(True)

    cdict = {0: 'green', 1: 'orange', 2: 'red'}
    labeldict = {0: 'Gutteil', 1: 'Nachbearbeiten', 2: 'Ausschuss'}

    for g in np.unique(cat):
        ix = np.where(cat == g)
        ax.scatter(L[ix], D[ix], T[ix], c = cdict[g], label = labeldict[g])

    ax.set_xlabel('Leistung in kW')
    ax.set_ylabel('Druck in bar')
    ax.set_zlabel('Temperatur in °C')
    ax.set_title('Trainingsdaten Station Lackieren')
    # plt.show()

    # do prediction on test data
    from sklearn.metrics import confusion_matrix
    y_pred = clf.predict(X_test)

    # plot a classification report
    from sklearn.metrics import classification_report
    report = classification_report(y_test, y_pred, output_dict=True)
    print(report)
    print(report['0.0']['precision'])

    # save test data, training data and classification in reort
    file = open("lackieren_knn_data_" + str(n_train) + ".csv", "w+")
    file.write(str(y_test.tolist()) + "\n")
    file.write(str(X_test.tolist()) + "\n")
    file.write(str(y_train.tolist()) + "\n")
    file.write(str(X_train.tolist()) + "\n")
    file.write(str(report) + "\n")
    file.close()

    # Create color maps
    cmap_light = ListedColormap(['green', 'orange', 'red'])
    cmap_bold = ListedColormap(['darkgreen', 'darkorange', 'darkred'])

    # Plot the decision boundary. For that, we will assign a color to each
    # point in the mesh [x_min, x_max]x[y_min, y_max].
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    z_min, z_max = X[:, 2].min() - 1, X[:, 2].max() + 1

    h = .04  # step size in the mesh
    h2 = 0.2
    xx_planeXY, yy_planeXY= np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
    xx_planeXZ, zz_planeXZ = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(z_min, z_max, h2))
    yy_planeYZ, zz_planeYZ = np.meshgrid(np.arange(y_min, y_max, h),
                         np.arange(z_min, z_max, h2))

    # prediction in XY (Leistung-Druck) plane with Z (Temperatur) fixed
    xx = xx_planeXY
    yy = yy_planeXY
    zz = np.ones(np.shape(xx_planeXY)) * 25

    V = clf.predict(np.c_[xx.ravel(), yy.ravel(), zz.ravel()])
    V = V.reshape(xx.shape)

    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111)

    plt.pcolormesh(xx, yy, V, cmap=cmap_light)

    plt.xlim(xx.min(), xx.max())
    plt.ylim(yy.min(), yy.max())

    plt.xlabel('Leistung in kN')
    plt.ylabel('Druck in bar')
    title = 'Klassifizierung für Temperatur = 32 °C'
    ax2.set_title(title, weight='bold', pad=20)
    plt.savefig('lackieren_train_temp_'+str(n_train)+'.png')
    # plt.show()

    # prediction in XZ (Leistung-Temperatur) plane with Z (Druck) fixed
    xx = xx_planeXZ
    yy = np.ones(np.shape(xx_planeXZ)) * 6
    zz = zz_planeXZ

    V = clf.predict(np.c_[xx.ravel(), yy.ravel(), zz.ravel()])
    V = V.reshape(xx.shape)

    fig3 = plt.figure()
    ax3 = fig3.add_subplot(111)
    plt.pcolormesh(xx, zz, V, cmap=cmap_light)

    plt.xlim(xx.min(), xx.max())
    plt.ylim(zz.min(), zz.max())

    plt.xlabel('Leistung in kW')
    plt.ylabel('Temperatur in Grad Celsius')
    title = 'Klassifizierung für Druck = 6 bar'
    ax3.set_title(title, weight='bold', pad=20)
    plt.savefig('lackieren_train_pressure_'+str(n_train)+'.png')
    # plt.show()

    # prediction in YZ (Druck-Temperatur) plane with Z (Leistung) fixed
    xx = np.ones(np.shape(yy_planeYZ)) * 1.5
    yy = yy_planeYZ
    zz = zz_planeYZ

    V = clf.predict(np.c_[xx.ravel(), yy.ravel(), zz.ravel()])
    V = V.reshape(xx.shape)

    fig4 = plt.figure()
    ax4 = fig4.add_subplot(111)
    plt.pcolormesh(yy, zz, V, cmap=cmap_light)

    plt.xlim(yy.min(), yy.max())
    plt.ylim(zz.min(), zz.max())

    plt.xlabel('Druck in bar')
    plt.ylabel('Temperatur in Grad Celsius')
    title = 'Klassifizierung für Leistung = 1.5kW'
    ax4.set_title(title, weight='bold', pad=20)
    plt.savefig('lackieren_train_power_'+str(n_train)+'.png')
    # plt.show()

    # Confusion Matrix on Test Data
    from sklearn.metrics import confusion_matrix
    y_pred = clf.predict(X_test)

    confusion_test = confusion_matrix(y_test, y_pred)

    # plot confusion matrix
    from sklearn.metrics import plot_confusion_matrix
    class_names = ['Gutteil', 'Nachbear.', 'Ausschuss']

    title = 'Konfusionsmatrix (absolut)'
    normalize = None
    disp = plot_confusion_matrix(classifier, X_test, y_test,
                                 display_labels=class_names,
                                 cmap=plt.cm.Blues,
                                 normalize=normalize,
                                 values_format='.0f')
    disp.ax_.set_title(title, weight='bold', pad=20)
    disp.ax_.set_xlabel('Vorhergesagte Klasse', weight='bold')
    disp.ax_.set_ylabel('Wahre Klasse', weight='bold')

    print(title)
    print(disp.confusion_matrix)
    plt.savefig('lackieren_confusion_absolute_'+str(n_train)+'.png')
    # plt.show()

    title = 'Konfusionsmatrix (normalisiert)'
    normalize = 'true'
    disp = plot_confusion_matrix(classifier, X_test, y_test,
                                 display_labels=class_names,
                                 cmap=plt.cm.Blues,
                                 normalize=normalize)
    disp.ax_.set_title(title, weight='bold', pad=20)
    disp.ax_.set_xlabel('Vorhergesagte Klasse', weight='bold')
    disp.ax_.set_ylabel('Wahre Klasse', weight='bold')

    print(title)
    print(disp.confusion_matrix)
    plt.savefig('lackieren_confusion_normalised_'+str(n_train)+'.png')

# call plotting function
plotting(n_train, n_neighbors)

