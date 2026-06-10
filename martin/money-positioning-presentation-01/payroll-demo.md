# Payroll Execution Demo

This demo application is included in the presentation as mentioned in README.md. It can be accessed from several slides of the presentation. The application should retain state thoughout the presentation. Regarless which slide is the application recalled from, the user should be presented with the same state where he left off with the application.

## Diagram

The slide will display a diagram with nodes representing various bank accounts:

- on the left side of the diagram, three nodes representing client companies ('Astra Inc', 'Bexel Ltd' and 'Cyra GmbH')
- in the middle, payroll bank accounts ('SVB', 'ACB' and 'BSB')
  - each bank can be toggled between active and inactive by clicking on the bank node
  - an inactive bank should be displayed as a darkened node
  - SVB and ACB should start as active, BSB as inactive
- on the right there should be nodes representing recepients:
  - 5 nodes for employees (Aiden Archer, Bianca Brooks, Caleb Carter, Diana Drake, Evan Ellery)
  - 4 nodes for tax agencies (FIT, NM SIT, NY MCTMT, NY SIT)
- each client company node should be connected by an arrow with a payroll bank account node indicating possible money movement
- each payroll bank account node should be connected by an arrow with each recipient account (employee, tax agency) indicating possible money movement

## Progression of Time

The application will simulate the progression of time in days. We will start with "Day 1". The top right corner of the application will have a calendar icon followed by a number indicating the current day. To the right of the number a shevron button should allow for progressing to the next day. In the instructions below "T" represents the current day.

## Running Payroll

When the user clicks on one of the client companies, an overlay should open allowing the user to put in data for payroll. 'Astra' is going to have 3 employees: Aiden, Bianca and  Caleb. 'Bexel' is going to employ Diana and Evan. 'Cyra' is going to employ Aiden and Evan.

The overlay should allow for entering earnings for each of the employees and a 'Run Payroll' button should be at the bottom of the overlay. An 'X' button in the top right corner of the overlay should allow the user to close the overlay without running a payroll. If the user runs a payroll we should create "ledger entries" (or "ledgers") representing all the transactions required to run the payroll. The following ledger entries should be created:

- funding ledger: transaction for the total amount of payroll from the client to the payroll bank acocunt configured for that client ('SVB' for Astra and 'ACB' for Bexel and Cyra). The due date of the funding ledger should be T+1

- wage disbursement ledgers: transaction from the payroll bank account configured for the given clinet to the employee specified in the payroll run. The transaction should be for 60% of the earnings entered for the payroll run (the remaining 40% will go to taxes). Due date for the transaction should be T+4.

- tax disbursement ledgers: based on the jurisdiction of where the employee lives, tax transactions should be generated. Below are the states where the employees live. If an employee lives in NY, the applicable taxes are FIT, NY MCTMT, NY SIT. If he lives in NM, the applicable taxes are FIT, NM SIT. Below are the tax rates and due dates for the agencies.

- Employee locations:
  - Aiden  - NY
  - Bianca - NY
  - Caleb  - NM
  - Diana  - NY
  - Evan   - NM

- Tax rates (percentage of earnings):
  - FIT - 20%
  - NY SIT - 10%
  - NY MCTMT - 10%
  - NM SIT - 20%

- Tax due dates:
  - FIT - T+6
  - NY SIT - T+10
  - NY MCTMT - T+12
  - NM SIT - T+12

## Ledger Representation

Each ledger should be displayed on the diagram. Each ledger has the following properties:
  - from bank account (the clients bank accounts for funding or payroll bank accounts for disbursements)
  - to bank account (payroll bank accounts for funding or eployee/tax-agency bank accounts for disbursements)
  - amount
  - due date (as a plain number - day X)

Each leddger should be represented as a box displaying the amount. The box should be placed on the line connecting the from and the to bank accounts. Prior to the due date, the ledger should be close to the from bank account. On and after the due date it should be close to the to bank account. Prior to the due date, the ledger should have a yellow tint (representing pending ledger). On and after the due date it should have a green tint (representing a completed ledger). Ledgers more then 5 days past their due date should start "fading" (becoming more transparent) with the ledger fully disappearing at 10 days past due.

If multiple ledgers are displayed in the same spot, they should be stacked (offset by a little bit from each other) with the ledger with the latest due date on top.

When the user advances the time, the state and placement of the ledgers can chnage. This transition should be animated.

## Company Payroll Configuration

The payroll overlay for a company should also include an option to select if this is a "Group A Company" or "Group B Company". This information is going to be used by the classifiers.

The group is a property of the **company**, not of an individual payroll run: it persists for the session and the classifiers always read the company's current group. Changing a company's group therefore re-affects all of that company's ledgers, including those from past payroll runs.

To make clear that this is company-level (not payroll-run) configuration, the group selector lives in a separate "Company Configuration" section placed below the "Run Payroll" button. When the "Active Payroll Runs" section is present, the "Company Configuration" section sits below that as well.

## Money Positioning based on Purpose

We are going to demonstrate the feature described in `narrative.md`. Positioning money based on clasifying a "purpose" for each ledger and then moving the money based on a "purpose" to payroll bank account configuration. This feature will not be active in the demo unless the slide that opens the demo explicitly states to include it.

When the feature is active, add two buttons to the top row, each opening its own configuration overlay:

- **"Classifiers"** (cogwheel icon) — opens an overlay listing all the classifiers; the user can toggle each between active and inactive. Initially all the classifiers are inactive. The state of the classifier should persist for the duration of the session. This overlay also holds the "Run money positioning automatically" selector with three choices: "Never", "At Beginning of Day", and "Every 4 Seconds". It defaults to "At Beginning of Day". When "Every 4 Seconds" is selected, the process runs automatically every 4 seconds (while the demo is open).
- **"Account Usage"** — opens an overlay with the "purpose" to bank account configuration. For each "purpose" it allows the user to select in which account the money should be.

Following is the list of classifiers:

- Purpose: "Investment" - Description: "Long Term Holdings"
   - applicable to ledgers that are from a payroll bank account and the due date is more than T+6.

- Purpose: "NM SIT" - Description: "New Mexico SIT Tax Funds"
   - applicable to ledgers where "to" is MN SIT bank account

- Purpose: "NY MCTMT" - Description: "New York MCTMT Tax Funds"
   - applicable to ledgers where "to" is NY MCTMT bank account

- Purpose: "WageDisbursement-GroupA" - Description: "Wage Disbursement for Group A Companies"
   - applicable to ledgers where "to" is an employee bank account and the company is in Group A.
   - applicable to ledgers where "from" is a company bank account and the company is in Group A.

- Purpose: "WageDisbursement-GroupB" - Description: "Wage Disbursement for Group B Companies"
   - applicable to ledgers where "to" is an employee bank account and the company is in Group B.
   - applicable to ledgers where "from" is a company bank account and the company is in Group B.

- Purpose: "TaxDisbursement-GroupA" - Description: "Tax Disbursement for Group A Companies"
   - applicable to ledgers where "to" is a tax-agency bank account and the company is in Group A.
   - applicable to ledgers where "from" is a company bank account and the company is in Group A.

- Purpose: "TaxDisbursement-GroupB" - Description: "Tax Disbursement for Group B Companies"
   - applicable to ledgers where "to" is a tax-agency bank account and the company is in Group B.
   - applicable to ledgers where "from" is a company bank account and the company is in Group B

Each classifier should be associated with a different colour.

### Executing Money Positioning

Money positioning can be executed in two ways:

- at the beginning of each day (if enabled in the configuration settings)
- manually by using a "Run Money Positioning" button in the top row.

To run money positioning, the following should happen:

- go over all ledgers that have not settled
- for each ledgers, go over the classifiers list (from top the bottom) and if any of the classifiers is applicable to the legdger, assign the purpose specified by the classifier by the ledger
  - in the graphic repesentation of the ledger, add a small circle at the top right corner colored based on the color of the purpose
  - based on the ledger purpose, look at the configuration that states in which bank account the money for the given purpose should be
  - determine the payroll bank account for the ledger (this can be the "to" bank account for funding ledgers or the "from" bank accout for disbursement ledgers)
  - if the payroll bank account on the ledger does not match the bank account stated by the purpose, the money needs to be redirected or moved
     - if the "to" bank account is the payroll bank account, the money is redirected - update the ledger's "to" bank account to be the one based on the purpose of the ledger, and also create an internal transfer ledger to move the money on to the bank account where it was originally expected. The internal transfer is from the purpose's account (the new "to") to the originally expected account (the old "to"), due on T+1, and associated with the same payroll run.
     - if the "from" bank account is the payroll bank account, the money has to be moved. Update the "from" bank account to the bank account based on the ledger purpose and create an internal transfer ledger between two payroll bank accounts. The internal transfer ledger should be due on T+1 (the next day) and it should be associated with the same payroll run as the original ledger. The internal transfer should be from the old payroll bank account on the original ledger to the new payroll bank accoun on the original ledger. This is to make sure that there is funding in the payroll bank account out of which the ledger is going to be ultimately paid. To represent these movements, you'll need to add arrows between payroll bank accounts. 
  - after creating the transfers, go over all internal transfer ledgers. If there are ledgers that are the opposite of each other in one payroll run, cancel those ledgers out by removing them from the system. E.G., if for payroll N there is a A->B transfer and a B->A transfer for the same amount - remove both transfers.