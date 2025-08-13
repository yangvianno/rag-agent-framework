# rag-agent-framework
# Technical Implementation Guide:
## Inventory Management MVP with a Separate Environments Architecture

---

### **Introduction: A New Approach for Absolute Data Isolation**

This document provides a comprehensive, phase-by-phase technical blueprint for developing an inventory management Minimum Viable Product (MVP) on the Microsoft Power Platform.

In response to the stakeholder requirement for **complete and physical data separation**, this guide adopts a **Separate Environments Architecture**. Instead of a single, shared database with logical security rules, this model provisions a unique, self-contained Power Platform Environment for each external partner. This approach guarantees that no partner's data will ever reside in the same database as another's, providing the highest possible level of data isolation.

#### **Core Project Goals:**
1.  **Centralized Internal Management**: Provide a single Power App for internal staff to manage inventory across all partner environments.
2.  **Isolated Partner Portals**: Offer each external partner a secure, dedicated Power Pages portal connected exclusively to their own private database.
3.  **Scalable Onboarding**: Establish a repeatable process for onboarding new partners into their own environments.

#### **Critical Trade-Offs of This Architecture:**
This approach successfully meets the demand for data separation but introduces significant trade-offs that must be acknowledged:
* **Higher Cost**: Each new environment requires its own Dataverse database capacity, which has direct and recurring licensing costs.
* **Increased Management Overhead**: Deploying updates or new features requires exporting the master solution and manually importing it into every single partner environment.
* **Greater Technical Complexity**: The internal Power App must be engineered to dynamically switch between different partner environment databases, which is more complex than connecting to a single source.

---

### **Phase 1: Build the Master Solution in the Development Environment**

**Goal**: Create a single, reusable, and deployable solution in your primary development environment that contains all the core components. This "master template" will be deployed to each partner environment.

**Technical Instructions:**

1.  **Select Your Development Environment**
    * Navigate to the Power Apps maker portal (`make.powerapps.com`).
    * From the environment selector in the top-right, choose your dedicated development environment (e.g., "Alex Vo's Environment"). **Do not build in the default environment.**

2.  **Create the Solution Publisher**
    * In the left navigation, select **Solutions**.
    * On the command bar, select **New solution**.
    * In the **Publisher** dropdown, select **+ Publisher**.
    * **Display Name**: `M4D LLC`
    * **Prefix**: `inv` (This is critical for uniquely identifying your components).
    * Select **Save**.

3.  **Create the Master Unmanaged Solution**
    * Back in the "New Solution" pane:
    * **Display Name**: `M4D Inventory Management - MASTER`
    * **Publisher**: Select the "M4D LLC (inv)" publisher you just created.
    * Select **Create**. From now on, **always work inside this solution**.

4.  **Create the `Product` Table**
    * Inside the solution, select **New > Table**.
    * **Display Name**: `Product`
    * Expand **Advanced options** and change the **Primary name column's Display Name** to `Product Description`.
    * Select **Save**.
    * Add all necessary columns based on your Excel file (`GTIN`, `SKU`, `Brand Name`, etc.).
    * For columns like `Status Label` and `Product Industry`, use the **Choice** data type to create standardized options.
    * **Important**: Do NOT add a lookup column to the `Account` table in this master solution. Since each partner has their own database, this relationship is not needed at the master level.

5.  **Build the Internal Power App**
    * Inside the solution, select **New > App > Canvas app**.
    * Build the internal staff application. It should include:
        * A gallery to view products.
        * Forms to edit and create products.
        * Barcode scanning functionality.
    * **Note**: For now, connect this app to the `Product` table in your development environment for testing. In a later phase, you will modify it to connect to multiple partner environments.

6.  **Create the Power Pages Site Template**
    * Inside the solution, select **New > App > Power Pages site**.
    * Design a generic portal template that can be deployed for each partner. Include:
        * A "My Products" page with a **List** component connected to the `Product` table.
        * A "Manage Product" page with a **Form** component for creating/editing records.
    * Do not provision the site fully yet; you are creating the template components that will be included in the solution.

---

### **Phase 2: Prepare and Export the Master Solution**

**Goal**: Package the master solution into a deployable file that can be imported into each new partner environment.

**Technical Instructions:**

1.  **Finalize and Test Components**
    * Thoroughly test the Power App and all components within your development environment to ensure they function as expected.

2.  **Export the Solution (Two Ways)**
    * Select your `M4D Inventory Management - MASTER` solution and click **Export solution** from the command bar.
    * **First Export (Unmanaged)**:
        * A side panel will appear. Click **Publish** to publish all changes first.
        * Click **Next**.
        * Select **Unmanaged** as the package type.
        * Click **Export**. This file is your editable backup and the master file for future development.
    * **Second Export (Managed)**:
        * Click **Export solution** again.
        * Select **Managed** as the package type.
        * Click **Export**. This locked-down file is what you will deploy to your partners. It prevents them from making direct modifications, ensuring consistency.

---

### **Phase 3: The Partner Onboarding Process (Repeatable Checklist)**

**Goal**: Follow this repeatable process every time you onboard a new external partner.

#### **Step 3.1: Create a New Partner Environment**
1.  Navigate to the [Power Platform Admin Center](https://admin.powerplatform.microsoft.com/).
2.  In the left navigation, select **Environments**, then click **+ New**.
3.  **Name**: Use a clear, consistent naming convention (e.g., `Partner A - Inventory`).
4.  **Region**: Choose the appropriate region.
5.  **Type**: Select **Production**.
6.  **Create a database for this environment?**: Toggle this to **Yes**. This is the most critical step.
7.  Click **Save**. Wait for the environment to finish provisioning.

#### **Step 3.2: Import the Managed Solution**
1.  Navigate to the newly created partner environment using the environment selector in the Power Apps portal.
2.  Go to **Solutions**.
3.  Click **Import solution** from the command bar.
4.  Select the **Managed** solution `.zip` file you exported in Phase 2.
5.  Follow the on-screen prompts to import the solution. This will create the `Product` table and all your app/portal components inside the partner's dedicated environment.

#### **Step 3.3: Provision the Power Pages Portal**
1.  In the partner environment, navigate to **Apps**.
2.  You will see the Power Pages site template you created. Select it.
3.  Follow the prompts to provision the site. Give it a unique name and URL (e.g., `partner-a-inventory.powerappsportals.com`).

#### **Step 3.4: Import Partner-Specific Data**
1.  Prepare an Excel file containing **only the data for that specific partner**.
2.  In the partner environment, navigate to your `Product` table (inside the imported solution).
3.  Select **Import > Import data from Excel** and upload the partner-specific file.

#### **Step 3.5: Configure Security and User Access**
1.  Add the partner's employees as guest users in your company's Microsoft Entra ID (Azure AD).
2.  Assign them the necessary Power Apps licenses.
3.  In the **Portal Management** app for the partner's new portal, navigate to **Security > Contacts** and add the partner users.
4.  Assign them the **Authenticated Users** web role. The security is simpler now because all data within this environment belongs to them, so complex rules are not needed.

---

### **Phase 4: Configure the Internal Multi-Environment Power App**

**Goal**: Modify your internal Power App to allow staff to select and manage inventory across any of the separate partner environments.

**Technical Instructions:**

1.  **Create a Partner Directory**
    * In your main development environment, create a new table named `Partner Directory`.
    * Add two columns: `Partner Name` (Text) and `Environment ID` (Text).
    * For each partner environment you create, find its unique Environment ID and add a new row to this table.
        * *Tip*: You can find the Environment ID in the Power Platform Admin Center by selecting the environment and looking at the details, or in the URL.

2.  **Modify the Internal Power App**
    * Open your internal Power App in the development environment.
    * On the home screen, add a **Dropdown** control.
    * Set the **Items** property of the dropdown to connect to your `Partner Directory` table:
        ```powerapps
        'Partner Directory'
        ```
    * Now, you must modify every Dataverse call in your app to use the selected partner's environment. For example, to view the products in a gallery, the `Items` property would change from `'Products'` to:
        ```powerapps
        Filter(
            [@Products],
            'Environment ID' = Dropdown1.Selected.'Environment ID'
        )
        ```
    * **Note**: This is an advanced technique. You are essentially parameterizing your data source connections. Every `Filter`, `LookUp`, `Patch`, and `SubmitForm` function that interacts with Dataverse must be updated to reference the environment selected in the dropdown.

---

### **Phase 5: Testing and Go-Live**

**Goal**: Verify that the data separation is absolute and all workflows function correctly.

**Technical Instructions:**

1.  **Onboard Two Test Partners**
    * Follow the complete checklist in Phase 3 to set up separate environments for "Partner A" and "Partner B".
    * Load Partner A's data into their environment and Partner B's data into theirs.

2.  **Test Portal Isolation**
    * Log into the Power Pages portal for Partner A. Confirm you can only see Partner A's products.
    * Log out and log into the portal for Partner B. Confirm you can only see Partner B's products.

3.  **Test Internal App Functionality**
    * Open the internal Power App.
    * Select "Partner A" from your environment-switching dropdown. Verify you can view and edit Partner A's inventory.
    * Switch the dropdown to "Partner B". Verify the app now shows Partner B's inventory and that you can manage it separately.
