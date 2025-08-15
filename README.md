# Technical Implementation Guide:
## Migrating Access Inventory to the Power Platform

---

**Document Version:** 1.1  
**Date:** August 14, 2025  
**Author:** Gemini Architect  
**Status:** Final

---

### **1.0 Introduction**

#### **1.1 Purpose**
This document provides a comprehensive, phase-by-phase technical blueprint for migrating the legacy Microsoft Access inventory database to a modern, secure, and scalable solution using Microsoft Dataverse, Power Apps, and Power Automate. It contains the complete data model, specific Power Fx formulas, and detailed automation logic required for a successful implementation. This guide is intended for Power Platform developers and administrators and is designed to be a repeatable blueprint for future deployments.

#### **1.2 Core Architecture: The Separate Environments Model**
The foundational architectural choice for this project is the **Separate Environments Model**. To meet the strict requirement for complete data privacy and security, each external partner will be provisioned with their own dedicated Power Platform environment, which includes a private Dataverse database. This model provides the highest level of data security through physical isolation.

**Key Trade-Offs:**
* **Cost:** Each environment requires its own Dataverse database capacity, incurring direct licensing costs.
* **Management:** Deploying updates requires exporting the master solution and importing it into each partner environment individually.

#### **1.3 Best Practices for This Guide**
It is highly recommended to capture and insert screenshots during the initial build for key configuration steps (e.g., Power Automate trigger setup, Portal Table Permissions) to supplement this guide for future reference.

---

### **2.0 Phase 1: Foundational Setup & Data Model Architecture**

#### **2.1 Initial Solution Setup**
All development work must occur within a dedicated solution to enable proper Application Lifecycle Management (ALM).

1.  **Create a Solution Publisher:**
    * Navigate to `make.powerapps.com` > **Solutions**.
    * Create a new **Publisher** with the following details:
        * **Display Name:** M4D LLC
        * **Prefix:** `inv`

2.  **Create the Master Unmanaged Solution:**
    * Create a new **Solution** with the following details:
        * **Display Name:** Inventory Management System - MASTER
        * **Publisher:** Select the publisher created above.

#### **2.2 Final Dataverse Data Model**
The following tables must be created inside the "Inventory Management System - MASTER" solution.

##### **2.2.1 Table: ProductList**
* **Purpose:** The master catalog of all products.
* **Primary Name Column:** `DESCRIPTION` (Data type: Text)
* **Columns:**
    * `ProductID` (Data type: Text, Alternate Key)
    * `Barcode` (Data type: Text) - This will be the scannable GTIN.
    * `Productclassification` (Data type: Text)
    * `PRODUCTGROUP` (Data type: Text)
    * `expiringdateyesorno` (Data type: Choice, Options: "Yes", "No")

##### **2.2.2 Table: CompanyInfo**
* **Purpose:** Stores partner and client company details.
* **Primary Name Column:** `Business` (Data type: Text)
* **Columns:**
    * `Address`, `AddressLine2`, `City`, `State`, `ZipCode`, `Country` (All Text)
    * `PhoneNumber` (Data type: Phone)

##### **2.2.3 Table: EnteredValues**
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

##### **2.2.4 Table: Backorder**
* **Purpose:** Manages primary order information.
* **Primary Name Column:** `OrderID` (Data type: Autonumber)
* **Columns:**
    * `Company` (Data type: **Lookup**, Related Table: `CompanyInfo`)
    * `PurchaseOrder` (Data type: Text)
    * `DateScannedIn2` (Data type: Date Only)
    * `Status` (Data type: Choice, Options: "Pending", "Backordered", "Shipped")

##### **2.2.5 Table: BackorderDetails**
* **Purpose:** Stores the individual line items for each backorder.
* **Primary Name Column:** `BackorderDetailID` (Data type: Autonumber)
* **Columns:**
    * `Backorder` (Data type: **Lookup**, Related Table: `Backorder`)
    * `Product` (Data type: **Lookup**, Related Table: `ProductList`)
    * `Quantity3` (Data type: **Whole Number**)

##### **2.2.6 Table: FedExIntegration**
* **Purpose:** Stores a complete, point-in-time snapshot of shipment details.
* **Primary Name Column:** `ShipmentNumber` (Data type: Text)
* **Columns:**
    * `Backorder` (Data type: **Lookup**, Related Table: `Backorder`)
    * `TrackingNumber` (Data type: Text)
    * `ShipmentLocation`, `Address`, `Address2`, `City`, `State`, `ZipCode`, `Country` (All Text)
    * `PhoneNumber` (Data type: Phone)
    * `Memo` (Data type: Text Area)
    * `Weight` (Data type: Decimal Number)

#### **2.3 Data Model Relationships**
The following relationships are critical for the system to function correctly. They will be created automatically when you create the Lookup columns defined above.

* `EnteredValues` to `ProductList` (Many-to-One)
* `Backorder` to `CompanyInfo` (Many-to-One)
* `BackorderDetails` to `Backorder` (Many-to-One)
* `BackorderDetails` to `ProductList` (Many-to-One)
* `FedExIntegration` to `Backorder` (Many-to-One)

---

### **3.0 Phase 2: Internal Warehouse Power App Implementation**

#### **3.1 Screen: MainMenu (Inventory Dashboard)**
This screen replicates the `MainMenu` form, providing a filterable, real-time view of inventory levels.

##### **3.1.1 Displaying Current Inventory**
* **Goal:** Replicate the `EnteredValuesQuery2` which uses `SUM(Quantity)` and `GROUP BY`.
* **Controls:** Add a Gallery control (`gal_InventorySummary`).
* **`Items` Property Formula for `gal_InventorySummary`:**
    ```powerapps
    // Group all transactions by the related Product and LotNumber,
    // then create a new column "TotalQuantity" that sums the Quantity for each group.
    AddColumns(
        GroupBy(
            EnteredValues,
            "Barcode", // This is the lookup column to the ProductList table
            "LotNumber",
            "GroupedTransactions" // A temporary name for the grouped data
        ),
        "TotalQuantity",
        Sum(GroupedTransactions, Quantity)
    )
    ```
* **Gallery Labels:** Inside the gallery, display the data using labels with these `Text` properties: `ThisItem.Barcode.DESCRIPTION`, `ThisItem.LotNumber`, `ThisItem.TotalQuantity`.

##### **3.1.2 Filtering the Inventory View**
* **Goal:** Replicate the live filtering from the Access form.
* **Controls:**
    * Add a **ComboBox** control named `ProductFilterCombo`. Set its `Items` property to `ProductList`.
    * Add a **Text input** control named `LotFilterInput`.
* **Updated `Items` Property Formula for `gal_InventorySummary`:**
    ```powerapps
    Filter(
        // This is the same GroupBy/AddColumns formula from the previous step
        AddColumns(
            GroupBy(EnteredValues, "Barcode", "LotNumber", "GroupedTransactions"),
            "TotalQuantity",
            Sum(GroupedTransactions, Quantity)
        ),
        // Filter Logic Start
        (IsBlank(ProductFilterCombo.Selected) || Barcode.Barcode = ProductFilterCombo.Selected.Barcode)
        &&
        (IsBlank(LotFilterInput.Text) || LotNumber = LotFilterInput.Text)
        // Filter Logic End
    )
    ```

#### **3.2 Screen: Data Entry (Add/Subtract Inventory)**
This screen replaces temporary tables (`UnitT`) with an in-app collection to stage data.

##### **3.2.1 Collecting Scanned Items into a Collection**
* **Goal:** Stage multiple scanned items in a temporary collection named `newInventoryItems`.
* **Control:** An "Add Item" Button.
* **`OnSelect` Property Formula:**
    ```powerapps
    With({_product: LookUp(ProductList, Barcode = txtBarcode.Text)},
        Collect(newInventoryItems, {
            ScannedBarcode: txtBarcode.Text,
            ProductID: _product.ProductID,
            LotNumber: txtLotNumber.Text,
            Quantity: Value(txtQuantity.Text),
            ShipmentNumber: "" // Placeholder for later update
        })
    );
    Reset(txtBarcode); Reset(txtLotNumber); Reset(txtQuantity);
    ```

##### **3.2.2 Updating All Items in the Collection**
* **Goal:** Apply a single `ShipmentNumber` to all staged items, replacing `UpdateUnitTQuery`.
* **Controls:** A Text input (`txtShipmentNumberForAll`) and a Button ("Apply to All").
* **"Apply to All" Button `OnSelect` Property Formula:**
    ```powerapps
    UpdateIf(newInventoryItems, true, { ShipmentNumber: txtShipmentNumberForAll.Text });
    Notify("Shipment Number applied to all items.", NotificationType.Information);
    ```

##### **3.2.3 Saving the Collection to Dataverse**
* **Goal:** Save all staged items to the `EnteredValues` table, replacing the `INSERT INTO` query.
* **Control:** A "Save" Button.
* **`OnSelect` Property Formula:**
    ```powerapps
    ForAll(newInventoryItems,
        Patch(EnteredValues, Defaults(EnteredValues), {
            Barcode: LookUp(ProductList, Barcode = ThisRecord.ScannedBarcode),
            ProductID: ThisRecord.ProductID,
            LotNumber: ThisRecord.LotNumber,
            Quantity: ThisRecord.Quantity, // For subtraction screen, use ThisRecord.Quantity * -1
            ShipmentNumber: ThisRecord.ShipmentNumber,
            DateScannedIn: Now()
        })
    );
    Clear(newInventoryItems);
    Notify("All items have been saved to the database.", NotificationType.Success);
    ```

---

### **4.0 Phase 3: Order Management & Partner Portal Logic**

#### **4.1 Creating Orders with Related Line Items**
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
                Quantity3: ThisRecord.Quantity,
                Backorder: newOrderRecord // This creates the relationship!
            })
        )
    );
    Clear(newOrderLines);
    Navigate(MainMenuScreen);
    ```

#### **4.2 Filtering Orders by Partner in Power Pages**
* **Goal:** Automatically filter orders to show only those belonging to the logged-in partner.
* **Method:** Use server-side **Table Permissions**, not a Power Fx formula.
* **Configuration Steps:**
    1.  Open the **Portal Management** app.
    2.  Go to **Security > Table Permissions** and create a new record.
    3.  **Settings:**
        * **Name:** `Partner Orders - Account Access`
        * **Table:** `Backorder`
        * **Access Type:** `Account Access`
        * **Relationship:** Select the schema name of the lookup from `Backorder` to `CompanyInfo`.
        * **Privileges:** Check `Read`.
    4.  Assign this permission to the **Authenticated Users** Web Role.
    5.  **Result:** Any list on the portal showing `Backorder` data will now be automatically and securely filtered for the logged-in user.

---

### **5.0 Phase 4: Automation with Power Automate**

#### **5.1 Automating Shipment Creation**
* **Goal:** Automatically create a `FedExIntegration` record when an order status changes to "Shipped".
* **Method:** An automated Power Automate cloud flow.
* **Flow Design:**
    1.  **Trigger:** Microsoft Dataverse - "When a row is added, modified or deleted"
        * **Change type:** `Modified`
        * **Table name:** `Backorder`
        * **Filter rows:** `statuscode eq <Value for 'Shipped'>` (Use the integer value for the "Shipped" status choice to optimize).
    2.  **Action 1:** Microsoft Dataverse - "Get a row by ID"
        * **Table name:** `CompanyInfo`
        * **Row ID:** Use the `Company (Value)` from the trigger output.
    3.  **Action 2:** Microsoft Dataverse - "Add a new row"
        * **Table name:** `FedExIntegration`
        * **Mapping:** Populate the fields using data from the trigger and the "Get a row by ID" action. For example:
            * `Backorder (Value)`: `OrderID` from the trigger.
            * `Address`: `Address` from the "Get a row by ID" step.
            * *(Continue mapping all address and other relevant fields)*

