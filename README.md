# Technical Implementation Guide:

## Migrating Access Inventory to the Power Platform



---



### **Introduction**



#### **A. Purpose**

This document provides a comprehensive, phase-by-phase technical blueprint for migrating the legacy Microsoft Access inventory database to a modern, secure, and scalable solution using Microsoft Dataverse, Power Apps, and Power Automate. It contains the complete data model, specific Power Fx formulas, and detailed automation logic required for a successful implementation. This guide is intended for Power Platform developers and administrators and is designed to be a repeatable blueprint for future deployments.



#### **B. How the Technology Works (For Non-Technical People)**

This inventory system is built using several Microsoft Power Platform tools that work together as a team. Here’s a simple breakdown of each component's role:



* **Microsoft Dataverse (The Central Brain & Database):** Think of Dataverse as the single, secure filing cabinet where all our important information is stored. Instead of scattered Access files, all data—products, partners, orders, and inventory logs—lives here. It’s smart, organized, and cloud-based, meaning the data is always up-to-date and accessible from anywhere.



* **Power Apps (The Tool for Internal Staff):** This is the custom application our internal team (e.g., warehouse staff, admins) will use on their computers, tablets, or phones. It’s the user-friendly interface for interacting with the data in Dataverse. When a warehouse user scans a product, they are using Power Apps to send that information directly to the Dataverse filing cabinet.



* **Power Pages (The Secure Website for Partners):** This is the private, secure web portal we create for each of our external partners. It connects to their dedicated Dataverse database and only shows them *their* information. It’s their window into our system, allowing them to see their inventory levels, check order history, and track shipments without being able to see any other partner's data.



* **Power Automate (The Automation Robot):** Think of Power Automate as a robot that handles repetitive, manual tasks for us. We can give it a set of rules, and it will work in the background 24/7. For example, instead of a person having to manually create a shipment record when an order is ready, we’ll teach our Power Automate robot to watch for any order whose status changes to "Shipped" and automatically create the shipment record for us. This saves time and reduces errors.



Together, these tools create a seamless, integrated system where data is securely stored (Dataverse), easily managed by our team (Power Apps), securely shared with partners (Power Pages), and intelligently automated (Power Automate).



#### **C. Core Architecture: The Separate Environments Model**

The foundational architectural choice for this project is the **Separate Environments Model**. To meet the strict requirement for complete data privacy and security, each external partner will be provisioned with their own dedicated Power Platform environment, which includes a private Dataverse database. This model provides the highest level of data security through physical isolation.



**Key Trade-Offs:**

* **Cost:** Each environment requires its own Dataverse database capacity, incurring direct licensing costs.

* **Management:** Deploying updates requires exporting the master solution and importing it into each partner environment individually.



#### **D. Best Practices for This Guide**

It is highly recommended to capture and insert screenshots during the initial build for key configuration steps (e.g., Power Automate trigger setup, Portal Table Permissions) to supplement this guide for future reference.



---



### **Phase 1: Foundational Setup & Data Model Architecture**



#### **1.1 Initial Solution Setup**

All development work must occur within a dedicated solution to enable proper Application Lifecycle Management (ALM).



1. **Create a Solution Publisher:**

* Navigate to `make.powerapps.com` > **Solutions**.

* Create a new **Publisher** with the following details:

* **Display Name:** M4D LLC

* **Prefix:** `inv`



2. **Create the Master Unmanaged Solution:**

* Create a new **Solution** with the following details:

* **Display Name:** M4D Inventory Management System - MASTER

* **Publisher:** Select the publisher created above.



#### **1.2 Final Dataverse Data Model**

The following tables must be created inside the "M4D Inventory Management System - MASTER" solution.



##### **1.2.1 Table: ProductList**

* **Purpose:** The master catalog of all products.

* **Primary Name Column:** `DESCRIPTION` (Data type: Text)

* **Columns:**

* `ProductID` (Data type: Text, Alternate Key)

* `Barcode` (Data type: Text) - This will be the scannable GTIN.

* `Productclassification` (Data type: Text)

* `PRODUCTGROUP` (Data type: Text)

* `expiringdateyesorno` (Data type: Choice, Options: "Yes", "No")



##### **1.2.2 Table: CompanyInfo**

* **Purpose:** Stores partner and client company details.

* **Primary Name Column:** `Business` (Data type: Text)

* **Columns:**

* `Address`, `AddressLine2`, `City`, `State`, `ZipCode`, `Country` (All Text)

* `PhoneNumber` (Data type: Phone)



##### **1.2.3 Table: EnteredValues**

* **Purpose:** The core transaction log for all inventory movements.

* **Primary Name Column:** `TransactionID` (Data type: Autonumber)

* **Columns:**

* `Barcode` (Data type: **Lookup**, Related Table: `ProductList`)

* `ProductID` (Data type: Text)

* `LotNumber` (Data type: Text)

* `DateScannedIn` (Data type: Date and Time)

* `ShipmentNumber` (Data type: Text)

* `ShipmentLocation` (Data type: Text)

* `Quantity` (Data type: **Whole Number**) - Use positive for additions, negative for subtractions.



##### **1.2.4 Table: Backorder**

* **Purpose:** Manages primary order information.

* **Primary Name Column:** `OrderID` (Data type: Autonumber)

* **Columns:**

* `Company` (Data type: **Lookup**, Related Table: `CompanyInfo`)

* `PurchaseOrder` (Data type: Text)

* `DateScannedIn2` (Data type: Date Only)

* `Status` (Data type: Choice, Options: "Pending", "Backordered", "Shipped")



##### **1.2.5 Table: BackorderDetails**

* **Purpose:** Stores the individual line items for each backorder.

* **Primary Name Column:** `BackorderDetailID` (Data type: Autonumber)

* **Columns:**

* `Backorder` (Data type: **Lookup**, Related Table: `Backorder`)

* `Product` (Data type: **Lookup**, Related Table: `ProductList`)

* `OrderedQuantity` (Data type: **Whole Number**)



##### **1.2.6 Table: FedExIntegration**

* **Purpose:** Stores a complete, point-in-time snapshot of shipment details.

* **Primary Name Column:** `ShipmentNumber` (Data type: Text)

* **Columns:**

* `Backorder` (Data type: **Lookup**, Related Table: `Backorder`)

* `TrackingNumber` (Data type: Text)

* `ShipmentLocation`, `Address`, `Address2`, `City`, `State`, `ZipCode`, `Country` (All Text)

* `PhoneNumber` (Data type: Phone)

* `Memo` (Data type: Text Area)

* `Weight` (Data type: Decimal Number)



#### **1.3 Data Model Relationships**

The following relationships are critical for the system to function correctly. They will be created automatically when you create the Lookup columns defined above.



* `EnteredValues` to `ProductList` (Many-to-One)

* `Backorder` to `CompanyInfo` (Many-to-One)

* `BackorderDetails` to `Backorder` (Many-to-One)

* `BackorderDetails` to `ProductList` (Many-to-One)

* `FedExIntegration` to `Backorder` (Many-to-One)



---



### **Phase 2: Internal Warehouse Power App Implementation**



#### **2.1 Configuring Internal Security Roles**

Before building the app, define the security roles in Dataverse to ensure proper access control for internal teams.



1. **Navigate to the Power Platform Admin Center**, select your development environment, and go to **Settings > Security roles**.

2. **Create the "Admin" Role:**

* Create a new role named `Inventory Admin`.

* For the tables `ProductList`, `CompanyInfo`, `EnteredValues`, `Backorder`, `BackorderDetails`, and `FedExIntegration`, grant full **Create, Read, Update, and Delete (CRUD)** permissions at the organization level.

3. **Create the "Warehouse" Role:**

* Create a new role named `Inventory Warehouse User`.

* Grant the following specific permissions:

* **ProductList:** Read access only.

* **EnteredValues:** Create and Read access.

* **Backorder & BackorderDetails:** Create and Read access.

* **No Delete access** on any of the primary tables.

4. **Assign Roles:** Assign these roles to the appropriate users or security groups.



#### **2.2 Implementing the Multi-Environment Connector**

This architecture requires the internal app to dynamically connect to different partner environments.



1. **Create a Partner Directory Table:**

* In your central development environment, create a new table named `PartnerDirectory`.

* Add two columns: `PartnerName` (Text) and `EnvironmentID` (Text).

* Populate this table with the name and unique Environment ID for each partner environment you provision.

2. **Add a Dropdown Selector to the App:**

* On the main screen of the internal Power App, add a **ComboBox** control named `PartnerSelector`.

* Set its `Items` property to the `PartnerDirectory` table.

3. **Dynamic Data Source Logic:**

* **Note:** True dynamic data source switching is an advanced topic. The simplest method is to add a separate data source connection for each partner's tables directly in the app (e.g., `EnteredValues_PartnerA`, `EnteredValues_PartnerB`).

* Use an `If()` or `Switch()` statement based on the `PartnerSelector` dropdown to choose which data source to query.

* **Example:**

```powerapps

// This formula chooses the correct data source based on the dropdown selection

Switch(PartnerSelector.Selected.PartnerName,

"Partner A", Filter(EnteredValues_PartnerA, ...),

"Partner B", Filter(EnteredValues_PartnerB, ...),

Blank() // Default case

)

```



#### **2.3 Screen: MainMenu (Inventory Dashboard)**

This screen provides a filterable, real-time view of inventory levels for the selected partner.



##### **2.3.1 Displaying Current Inventory**

* **`Items` Property Formula for `gal_InventorySummary`:**

```powerapps

// This formula must be wrapped in the Switch logic from section 3.2

// Example for a single partner:

AddColumns(

GroupBy(

EnteredValues_PartnerA, // Note the partner-specific data source

"Barcode",

"LotNumber",

"GroupedTransactions"

),

"TotalQuantity",

Sum(GroupedTransactions, Quantity)

)

```



#### **2.4 Screen: Data Entry (Add/Subtract Inventory)**

This screen uses an in-app collection to stage data before saving to the selected partner's environment.



##### **2.4.1 Saving the Collection to Dataverse**

* **`OnSelect` Property Formula for the "Save" Button:**

```powerapps

// Use a Switch statement to target the correct environment's table

Switch(PartnerSelector.Selected.PartnerName,

"Partner A",

ForAll(newInventoryItems, Patch(EnteredValues_PartnerA, Defaults(EnteredValues_PartnerA), {...})),

"Partner B",

ForAll(newInventoryItems, Patch(EnteredValues_PartnerB, Defaults(EnteredValues_PartnerB), {...}))

);

Clear(newInventoryItems);

Notify("All items have been saved.", NotificationType.Success);

```



#### **2.5 Implementing Role-Based Visibility in the App**

* **Control Screen Access:** On the app's `OnStart` or main screen, you can direct users based on their role.

```powerapps

// This requires setting up a security group or list of admin emails

If(User().Email in ["admin1@company.com", "admin2@company.com"],

Set(isAdmin, true),

Set(isAdmin, false)

);

```

* **Control Button Visibility:** Set the `Visible` property of admin-only controls (e.g., an "Edit Products" button).

```powerapps

isAdmin // This will be true or false based on the logic above

```



---



### **Phase 3: Order Management Logic**



#### **3.1 Creating Orders with Related Line Items**

* **Goal:** Create a main `Backorder` record, then use its ID to create multiple related `BackorderDetails` records.

* **Assumption:** An in-app collection `newOrderLines` holds the products for the new order.

* **"Save Order" Button `OnSelect` Property Formula:**

```powerapps

// Step 1: Create the main Backorder record and store it in a variable.

With({ newOrderRecord:

Patch(Backorder, Defaults(Backorder), {

PurchaseOrder: txtPONumber.Text,

Company: partnerDropdown.Selected,

DateScannedIn2: Today(),

Status: 'Status (Backorder)'.Pending

})

},

// Step 2: Loop through the newOrderLines collection and create related records.

ForAll(newOrderLines,

Patch(BackorderDetails, Defaults(BackorderDetails), {

Product: ThisRecord.ProductLookup,

OrderedQuantity: ThisRecord.Quantity,

Backorder: newOrderRecord // This creates the relationship!

})

)

);

Clear(newOrderLines);

Navigate(MainMenuScreen);

```



---



### **Phase 4: Partner Portal Implementation (Power Pages)**



#### *4.1 Provisioning the Partner Portal**

For each new partner environment, you must provision a Power Pages site.



1. Navigate to the partner's environment via `make.powerapps.com`.

2. Go to **Solutions** and open the imported `M4D Inventory Management System` solution.

3. Click **New > App > Power Pages site**.

4. Select a starter template, give the site a unique name (e.g., `PartnerA-InventoryPortal`), and click **Done**. The provisioning process may take several minutes.



#### **4.2 Building the Portal User Interface**

Use the Power Pages design studio to create the user-facing pages.



1. **Create Web Pages:**

* Create the necessary pages: `Home`, `Inventory Status`, `Order History`, and `Shipment Tracking`.

2. **Add Components to Pages:**

* **On the `Inventory Status` page:** Add a **List** component. Configure it to show data from the `EnteredValues` table. You will likely want to create a specific Dataverse View for this that summarizes the data.

* **On the `Order History` page:** Add a **List** component configured to show data from the `Backorder` table.

3. **Enable Actions on Lists:**

* In the List component's settings, you can enable actions like "View Details". This action will navigate the user to a page containing a **Read-only Form** component, showing all the details of the selected record (e.g., all line items for an order).



#### **4.3 Securing Portal Data with Table Permissions**

This is the most critical step for ensuring partners only see their own data.



1. Open the **Portal Management** app for the specific partner's portal.

2. Go to **Security > Table Permissions** and create a new record for each table you want to expose.

3. **Example Configuration for Orders:**

* **Name:** `Partner Orders - Account Access`

* **Table:** `Backorder`

* **Access Type:** `Account Access`

* **Relationship:** Select the schema name of the lookup from `Backorder` to `CompanyInfo`.

* **Privileges:** Check `Read`.

4. **Assign to Web Role:** Go to **Web Roles** and open the **Authenticated Users** role. Add the new Table Permission to this role.

5. **Result:** Any list on the portal showing `Backorder` data will now be automatically and securely filtered for the logged-in user's company. Repeat this process for all other tables (`EnteredValues`, `FedExIntegration`, etc.).



#### **4.4 Configuring Partner Authentication with Microsoft Entra External ID**

This provides a secure, professional login experience for your partners.



1. **Step 1: Set up in Azure Portal (High-Level)**

* Navigate to the **Azure Portal** (`portal.azure.com`).

* Create a new **Microsoft Entra ID** tenant, selecting the **External** configuration (this creates a tenant for customers/partners).

* Inside the new tenant, create an **App registration** for your Power Pages site.

* In the app registration's **Authentication** settings, add a platform for **Web** and paste the **Reply URL** provided by your Power Pages site.

* Under **External Identities**, create a **User flow** for "Sign up and sign in". This defines the experience your partners will have when they register and log in.

2. **Step 2: Configure in Power Pages**

* In the Power Pages design studio, go to the **Set up** workspace > **Identity providers**.

* Next to **Microsoft Entra External ID**, select **Configure**.

* Follow the wizard, pasting the **Application (client) ID** and other details from your Azure app registration.

3. **Step 3: Invite Partners**

* Once configured, you can create **invitations** from within the Portal Management app. This sends a unique link to a partner contact, allowing them to redeem the invitation, register their account via the Entra External ID user flow, and sign in to the portal.



---



### **Phase 5: Automation and Document Generation**



#### **5.1 Automating Shipment Creation with Power Automate**

* **Goal:** Automatically create a `FedExIntegration` record when an order status changes to "Shipped". This replaces a manual data entry step from the Access database.

* **Method:** An automated Power Automate cloud flow.

* **Flow Design:**

1. **Trigger:** Microsoft Dataverse - "When a row is added, modified or deleted"

* **Change type:** `Modified`

* **Table name:** `Backorder`

* **Filter rows:** `statuscode eq <Value for 'Shipped'>` (Use the integer value for the "Shipped" status choice to optimize).

2. **Action 1:** Microsoft Dataverse - "Get a row by ID"

* **Table name:** `CompanyInfo`

* **Row ID:** Use the `Company (Value)` from the trigger output.

3. **Action 2:** Microsoft Dataverse - "Add a new row"

* **Table name:** `FedExIntegration`

* **Mapping:** Populate the fields using data from the trigger and the "Get a row by ID" action. For example:

* `Backorder (Value)`: `OrderID` from the trigger.

* `Address`: `Address` from the "Get a row by ID" step.

* *(Continue mapping all address and other relevant fields)*



#### **5.2 Generating Packing Slips with Word Online & Power Automate**

* **Goal:** Allow a warehouse user to generate a professional, formatted packing slip document from an order.

* **Method:** A Power Automate flow connected to a pre-formatted Microsoft Word template.



##### **5.2.1 Step 1: Create the Word Template**

1. Open Microsoft Word (desktop or online).

2. Design the layout of your packing slip. Include your company logo, addresses, and tables.

3. For every piece of data that will be dynamic (e.g., partner's address, product ID), you must insert a **Plain Text Content Control**.

4. To enable content controls, you may need to enable the "Developer" tab in Word's options.

5. Give each content control a unique and descriptive name in its properties (e.g., `PartnerName`, `ShipmentDate`, `ProductID`).

6. For the list of products, create a table with one row. Place content controls for `ProductID`, `Part Description`, `LotNumber`, etc., in the cells of that single row.

7. Save this `.docx` file to a SharePoint document library or OneDrive folder that Power Automate can access.



##### **5.2.2 Step 2: Create the Power Automate Flow**

1. **Trigger:** In the Power App, add a button "Generate Packing Slip". Its `OnSelect` property will trigger the flow:

```powerapps

// 'GeneratePackingSlip' is the name of your Power Automate flow

// Pass the ID of the selected order from your gallery (gal_Orders)

GeneratePackingSlip.Run(gal_Orders.Selected.OrderID);

Notify("Packing slip is being generated...", NotificationType.Information);

```

2. **Flow Action 1: Get Order Details**

* Use the Dataverse action "Get a row by ID" to retrieve all details for the `Backorder` record using the ID passed from Power Apps.

3. **Flow Action 2: Get Order Line Items**

* Use the Dataverse action "List rows". Select the `BackorderDetails` table and use a filter query to retrieve only the line items related to the order ID from the trigger (e.g., `_inv_backorder_value eq '[Order ID]'`).

4. **Flow Action 3: Populate a Microsoft Word template**

* Select the **Word Online (Business)** connector.

* Choose the template file you created in Step 1.

* The action will display all the content controls you created. Map the data from the "Get Order Details" step to the appropriate fields (e.g., `PartnerName`, `ShipmentDate`).

* For the repeating product list, this action will automatically detect your table and allow you to map the values from the "Get Order Line Items" step.

5. **Flow Action 4: Create file**

* Use a SharePoint or OneDrive action to save the newly generated Word document. You can use dynamic content to give it a unique name (e.g., `PackingSlip_[OrderID].docx`).

6. **Flow Action 5 (Optional): Send Email**

* Add an action to send an email to the user with the generated packing slip as an attachment.



---



### **Phase 6: Deployment and Application Lifecycle Management (ALM)**



#### **6.1 Exporting the Master Solution**

Before deploying to any partner environment, the master solution must be exported correctly from the development environment.



1. Navigate to your `M4D Inventory Management System - MASTER` solution.

2. Click **Publish all customizations**.

3. Click **Export solution**.

4. Select **Managed** as the package type. A managed solution is locked and prevents modifications in production environments, ensuring consistency and stability.

5. Export the solution and save the resulting `.zip` file. This is your deployment artifact.



#### **6.2 The Partner Onboarding Process Checklist**

Follow this checklist for each new partner to ensure a consistent and secure setup.



1. **[ ] Create the Partner Environment:**

* In the Power Platform Admin Center, create a new **Production** environment.

* Ensure you enable the option to **Create a database for this environment**.

2. **[ ] Import the Managed Solution:**

* Navigate to the new partner environment.

* Go to **Solutions > Import solution** and select the **managed** `.zip` file you exported.

3. **[ ] Add Data Source to Internal App:**

* Open the internal Power App and add a new data connection to the `EnteredValues` and other relevant tables from the newly created partner environment.

* Update the `Switch()` formulas on the app's screens to include the new partner.

4. **[ ] Update the Partner Directory:**

* Add a new row to your `PartnerDirectory` table with the new partner's name and their Environment ID.

5. **[ ] Run Initial Data Import:**

* Prepare a data file with the partner's initial product list and inventory.

* Use the data import wizard in the partner's environment to load this data into the `ProductList` and `EnteredValues` tables.

6. **[ ] Assign User Security Roles:**

* Add the partner's employees as users in the environment.

* Assign them the necessary security roles for the Power Pages portal (e.g., Authenticated Users).
