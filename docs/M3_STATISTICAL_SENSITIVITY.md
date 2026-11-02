# M3 prior, optimizer and statistical sensitivity

## Prior strength, separate MAP experiments

Two MAP stellar prior widths, 0.05 and 0.2 dex, bracket the 0.1-dex fiducial. Centers 0.5/0.7, geometry priors, positive domains, all physical boxes and the same deterministic M2 starts are unchanged. Widths are prior-strength stress cases, not measured populations. No concentration-mass or other cosmological halo prior is added; such a relation would change the physical hypothesis. Counts by width/status: {(0.05, 'CONVERGED'): 697, (0.2, 'CONVERGED'): 696, (0.05, 'NO_VALID_START'): 3, (0.2, 'NO_VALID_START'): 4}.

Per-parameter changes, data chi², prior penalty and boundary/conditioning outputs are retained in prior_sensitivity.json. No MAP AIC/AICc/BIC or cross-prior posterior-evidence ranking is calculated. Different prior widths can select different ridge locations without new information. The new adapter at 0.1 dex reproduced frozen M2 MAP parameters/predictions for 12 real galaxy/model cases before M3 fitting. No legacy source was edited.

## Optimizer checks

Each physical halo scenario uses four deterministic M2 initializations; nuisance MAP starts also remain unchanged. All attempts, domain aborts, objective ranges and ranges among solutions within delta objective<=1 are retained. 10 galaxy/scenario/halo records show >0.1 dex spread among such near-objective solutions; this flags practical ambiguity, not proof of posterior multimodality. Identical repeats do not prove physical identifiability.

Independent dogbox trust-region checks covered six frozen galaxies × three scenarios × two halos =36 problems, with two starts, unchanged bounds and 1e-6 relative objective agreement target. 33 comparable cases agree; three UGC01281 Burkert cases yield no feasible pair under the frozen domain/search policies. Their failures are visible, not proof of physical model nonexistence. Parameter differences despite objective agreement are in optimizer_method_parameter_changes.json. No bound was narrowed or failed solution counted successful.

## Likelihood-comparison choices

AIC/AICc/BIC alternatives use identical data/likelihoods and the common M2 regular-eligibility gate. The operational decisive gap stays 2. At the M2 baseline, changing from AICc changes decision/winner status in 7/175 cases for AIC and 7/175 for BIC. Across applicable physical scenarios, decision/winner changes are 29 / 1792 for AIC and 32 / 1792 for BIC; their valid comparison denominators are separately stored. No criterion choice is pooled into primary physical persistence fractions.

Predicted performance, ML criterion penalties, MAP objectives, parameter plausibility and curve adequacy are different quantities. None becomes a probability that a gravity theory is true. No MCMC, bootstrap probability calibration, new global acceleration fitting or full stochastic uncertainty campaign was run. This bounded deterministic design and its stored parameter/likelihood ranges are the declared uncertainty experiment.
