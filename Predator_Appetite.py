import numpy as np
import scipy as sp
import scipy.optimize as opt
import scipy.integrate as spi
from scipy.integrate import odeint
from scipy.integrate import solve_ivp
import csv
import matplotlib.pyplot as plt

filename = 'MDM/GP2/Hare_Lynx_Data.csv'

with open(filename, newline ='') as file:
    reader = csv.reader(file, delimiter=',', quotechar='|')
    next(reader)  # Skip header
    year, hare, lynx = [], [], []
    for row in reader:
        year.append(int(row[0]))
        hare.append(float(row[1]))
        lynx.append(float(row[2]))
    data = year, hare, lynx


# plot the data
def plot_data(data):
    plt.plot(year, hare, label='Hare Population', color='cornflowerblue')
    plt.plot(year, lynx, label='Lynx Population', color='lightcoral')
    plt.xlabel('Time (Years)')
    plt.ylabel('Population (Thousands)')
    plt.title('Hare and Lynx Population Dynamics')
    plt.legend()
    plt.show()

plot_data(data)


# Estimate instrinsic growth rate of hares (alpha):

alpha_values = []  # % change in hares per year

for i in range(len(hare)-1):
    H_0 = hare[i]
    H_1 = hare[i + 1]
    
    percentage_change = (hare[i+1] - hare[i]) / hare[i]  # % change in hares per year
    alpha_values.append(percentage_change)

alpha_est = np.mean(alpha_values)  # Average growth rate
print(f"Estimated Alpha: {alpha_est:.4f}")

K_est = max(hare)
print(f"Estimated Carrying Capacity (K): {K_est}")


# Compute f(H): 'hares eaten per lynx per year'

f_H = []  # Hares eaten per lynx per year
H_vals = []  # Hare population values


for i in range(len(hare) - 1):
    
    H_0 = hare[i]
    H_1 = hare[i + 1]
    L_0 = lynx[i]

    if L_0 == 0 or H_0 == 0 or (H_0 - H_1) <= 0:
        continue

    
    f_value =  (alpha_est * H_0 - (H_1 - H_0)) / L_0  # Hares eaten per lynx per year
    print(year[i], ':', f"Number of Hares: {H_0}", '  ,  ', f"Hares Eaten per Lynx: {f_value:.4f}")
    
    f_H.append(f_value)
    H_vals.append(H_0)
    

    

# Convert to arrays: 
H_vals = np.array(H_vals)
f_H = np.array(f_H)


# Holling Type II Model: f(H) = (a * H) / (1 + a * h * H)
def hollings_type(H, a, h):
    return a * H/ (1 + a * h * H)


# Fit non-linear least squares: to estimate a and h

params, covariance = opt.curve_fit(hollings_type, H_vals, f_H, p0=[0.1, 0.1])
a_fit, h_fit = params
print(params)
print(f"Estimated Capture Rate (a): {a_fit:.4f}")
print(f"Estimated Handling Time (h): {h_fit:.4f}")


# Plot the fit
plt.scatter(H_vals, f_H,label='Data', c='blue', s=20, marker='x')
H_fit = np.linspace(min(H_vals), max(H_vals), 100)  # Hare population values
plt.plot(H_fit, hollings_type(H_fit, a_fit, h_fit), label='Holling Type II Fit', color='red')
plt.xlabel('Hare Population')
plt.ylabel('Hares Eaten per Lynx')
plt.title('Estimating a and h using NonLinear Least Squares')
plt.legend()
plt.show()


# Parameter Estimation
params = [
hare[0], # H0
lynx[0], # L0
alpha_est,  # alpha
a_fit, # beta
a_fit,  # a
h_fit,  # h
0.5, # gamma
0.98, # delta
np.linspace(year[0], year[-1], 10000), # time
K_est # K
] 


# Original Predator-Prey Model

def original_model(params):
    H0, L0, alpha, beta, a, h, gamma, delta, t, K = params
    delta = 1-delta
    
    def predator_prey_model(y, t, alpha, beta, gamma, delta):
        H, L = y
        dH_dt = alpha * H - beta * H * L
        dL_dt = - gamma * L + delta * H * L
        return [dH_dt, dL_dt]

    y0 = [H0, L0]
    solutions = odeint(predator_prey_model, y0, t, args=(alpha, beta, gamma, delta))

    H, L = solutions.T

    return H, L, 'Original Predator v Prey'


    


# Modified Predator-Prey Model
def modified_model(params):

    H0, L0, alpha, beta, a, h, gamma, delta, t, K = params    

    def predator_prey_model(y, t, alpha, a, h, delta, gamma):
        H, L = y
        dH_dt = alpha * H - hollings_type(H,a,h) * L
        dL_dt = -gamma * L + hollings_type(H,a,h) * L * delta
        return [dH_dt, dL_dt]

    y0 = [H0, L0]
    solutions = odeint(predator_prey_model, y0, t, args=(alpha, a, h, delta, gamma))
    H, L = solutions.T

    return H, L, 'Functional Response'


# Adding to NonLinear prey growth assumption
def nonlinear_and_appetite_model(params):

    H0, L0, alpha, beta, a, h, gamma, delta, t, K = params

    def appetite_and_prey_growth(y, t, alpha, a, h, delta, gamma, K):
        H, L = y
        dH_dt = alpha * H * (1 - H/K) - hollings_type(H,a,h) * L
        dL_dt = -gamma * L + hollings_type(H,a,h) * L * delta
        return [dH_dt, dL_dt]

    y0 = [H0, L0]
    solutions = odeint(appetite_and_prey_growth, y0, t, args=(alpha, a, h, delta, gamma, K))
    H, L = solutions.T

    return H, L, 'Functional Response & Nonlinear Growth of Prey'



def plot_model(params, model, show, original, dotted, split):
    H0, L0, alpha, beta, a, h, gamma, delta, t, K = params
    H, L, title = model

    Ho, Lo, title_original = original_model(params)
    if title == title_original:
        if split == True:
            # Hare Plot
            plt.subplot(2,1,1)
            plt.plot(year, hare, '--', label='Hare (Data)', color='cornflowerblue')
            if original == True:
                plt.plot(t, Ho, label='Hares (Original)', color = 'turquoise')
            plt.plot(t, H, label='Hares (Modified)', color = 'blue')
            plt.xlabel('')
            plt.ylabel('Population (Thousands)')
            plt.title(f"Population Dynamics: {title}")
            plt.legend(loc = 'upper right')

            # Lynx Plot
            plt.subplot(2,1,2)
            plt.plot(year, lynx, '--', label='Lynx (Data)', color='lightcoral')
            if original == True:
                plt.plot(t, Lo, label='Lynx (Original)', color = 'mediumorchid')
            plt.plot(t, L, label='Lynx (Modified)', color = 'red')
            plt.xlabel('Time (Years)')
            plt.ylabel('Population (Thousands)')
            plt.title(' ')
            plt.legend(loc = 'upper right')

        else:
            if original == True:
                plot_model(params, original_model(params), False, False, True, False)
            if dotted == True:
                plt.plot(t, H, '--', label='Hares (Original)', color = 'cornflowerblue')
                plt.plot(t, L, '--', label='Lynx (Original)', color = 'lightcoral')
                plt.xlabel('Time (Years)')
                plt.ylabel('Population (Thousands)')
                plt.title(title)
                plt.legend(loc = 'upper right')

            else:
                
                plt.plot(t, H, label='Hares (Modified)', color = 'blue')
                plt.plot(t, L, label='Lynx (Modified)', color = 'red')
                plt.xlabel('Time (Years)')
                plt.ylabel('Population (Thousands)')
                plt.title(f"Original Lokta-Volterra")
                plt.legend(loc = 'upper right')
                

    else:
        if split == True:
            # Hare Plot
            plt.subplot(2,1,1)
            plt.plot(year, hare, '--', label='Hare (Data)', color='cornflowerblue')
            if original == True:
                plt.plot(t, Ho, label='Hares (Original)', color = 'turquoise')
            plt.plot(t, H, label='Hares (Modified)', color = 'blue')
            plt.xlabel('')
            plt.ylabel('Population (Thousands)')
            plt.title(f"Population Dynamics: {title}")
            plt.legend(loc = 'upper right')

            # Lynx Plot
            plt.subplot(2,1,2)
            plt.plot(year, lynx, '--', label='Lynx (Data)', color='lightcoral')
            if original == True:
                plt.plot(t, Lo, label='Lynx (Original)', color = 'mediumorchid')
            plt.plot(t, L, label='Lynx (Modified)', color = 'red')
            plt.xlabel('Time (Years)')
            plt.ylabel('Population (Thousands)')
            plt.title(' ')
            plt.legend(loc = 'upper right')

        else:
            if original == True:
                plot_model(params, original_model(params), False, False, True, False)
            if dotted == True:
                plt.plot(t, H, '--', label='Hares (Original)', color = 'cornflowerblue')
                plt.plot(t, L, '--', label='Lynx (Original)', color = 'lightcoral')
                plt.xlabel('Time (Years)')
                plt.ylabel('Population (Thousands)')
                plt.title(title)
                plt.legend(loc = 'upper right')

            else:
                
                plt.plot(t, H, label='Hares (Modified)', color = 'blue')
                plt.plot(t, L, label='Lynx (Modified)', color = 'red')
                plt.xlabel('Time (Years)')
                plt.ylabel('Population (Thousands)')
                plt.title(f"Updated Model with {title}")
                plt.legend(loc = 'upper right')
                


    if show == True:
        plt.show()

    return H, L



# Run the models
plot_model(params, original_model(params), True, False, False, False)

plot_model(params, modified_model(params), True, True, False, False)
plot_model(params, modified_model(params), True, True, False, True)

plot_model(params, nonlinear_and_appetite_model(params), True, True, False, False)
plot_model(params, nonlinear_and_appetite_model(params), True, True, False, True)



def plot_residuals_comparison(params, modified_model_func):
    H_data = np.array(hare)
    L_data = np.array(lynx)
    t_data = np.array(year)
    
    # Get model predictions
    H_mod, L_mod, mod_title = modified_model_func(params)
    H_lotka, L_lotka, lotka_title = original_model(params)
    
    # Interpolate to match data points
    H_mod_interp = np.interp(t_data, params[8], H_mod)
    L_mod_interp = np.interp(t_data, params[8], L_mod)
    
    H_lotka_interp = np.interp(t_data, params[8], H_lotka)
    L_lotka_interp = np.interp(t_data, params[8], L_lotka)
    
    # Compute residuals
    hare_residuals_mod = H_data - H_mod_interp
    lynx_residuals_mod = L_data - L_mod_interp
    
    hare_residuals_lotka = H_data - H_lotka_interp
    lynx_residuals_lotka = L_data - L_lotka_interp
    
    # Plot residuals comparison
    plt.figure(figsize=(12, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(t_data, hare_residuals_lotka, '--', color='cornflowerblue', label='Hare Residuals (Lotka-Volterra)')
    plt.plot(t_data, hare_residuals_mod, color='blue', label=f'Hare Residuals ({mod_title})')
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.xlabel('Time (Years)')
    plt.ylabel('Residuals')
    plt.legend(loc='lower left')
    
    plt.subplot(2,1,2)
    plt.plot(t_data, lynx_residuals_lotka, '--', color='lightcoral', label='Lynx Residuals (Lotka-Volterra)')
    plt.plot(t_data, lynx_residuals_mod, color='red', label=f'Lynx Residuals ({mod_title})')
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.xlabel('Time (Years)')
    plt.ylabel('Residuals')
    plt.legend(loc='lower left')
    
    
    
    
    plt.suptitle(f'Residuals Comparison: Lotka-Volterra vs {mod_title}')
    plt.tight_layout()
    plt.show()

# Compare residuals for both models
plot_residuals_comparison(params, modified_model)
plot_residuals_comparison(params, nonlinear_and_appetite_model)


print(params)