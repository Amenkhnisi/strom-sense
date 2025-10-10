export interface BillingPeriod {
  start_date: string | null;
  end_date: string | null;
}

export interface NextInstallment {
  amount: string | number | null;
  due_date: string | null;
}

export interface FieldValue<T = any> {
  raw: string | null;
  normalized: T | null;
  confidence: number;
}

export interface ParsedInvoiceData {
  supplier: string; // e.g. "EON" | "GREEN_PLANET"
  supplierName?: FieldValue<string>;
  customerId?: FieldValue<string>;
  contractNumber?: FieldValue<string>;
  invoiceId?: FieldValue<string>;
  meterNumber?: FieldValue<string>;
  billingPeriod?: FieldValue<BillingPeriod>;
  totalConsumption?: FieldValue<number>;
  totalAmount?: FieldValue<number>;
  issueDate?: FieldValue<string>;
  paymentsMade?: FieldValue<number>;
  balance?: FieldValue<number>;
  balanceType?: FieldValue<string>;
  nextInstallment?: FieldValue<NextInstallment>;
  workPrice?: FieldValue<number>;
  basicFee?: FieldValue<number>;
  vatRate?: FieldValue<number>;
}
