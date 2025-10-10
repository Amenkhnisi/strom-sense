import { useState } from "react";
import axios from "axios";
import FileUpload from "./FileUpload";
import { SpaceIcon } from "lucide-react";
import type { ParsedInvoiceData } from "../types/ParsedInvoiceData";
import VerificationPanel from "./VerificationPanel";


const BillInput = () => {
    const [formData, setFormData] = useState({
        monthly_kwh: "",
        billing_date_from: "",
        billing_date_to: "",
        supplier_name: "",
        total_amount: "",
    });
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [parsedData, setParsedData] = useState<any>(null);

    // 1. Handle manual input
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // 2. Receive file from FileUpload component
    const handleFileSelect = (file: File) => {
        setSelectedFile(file);

    };

    // 3. Hande save 
    const handleSave = (updatedData: ParsedInvoiceData) => {
        console.log('Saved data:', updatedData);
        alert('✅ Data saved successfully!');
    };


    // 3. Submit form + file to backend
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        try {
            let mergedData = { ...formData };

            if (selectedFile) {
                const form = new FormData();
                form.append("file", selectedFile);

                const res = await axios.post("http://localhost:5000/upload-bill/", form);
                const ocr = res.data.parsed_data || {};
                const parsed: ParsedInvoiceData = ocr;

                console.log(parsed)

                // Merge OCR results with manual form data
                mergedData = {
                    ...mergedData,
                    monthly_kwh: ocr.totalConsumption || formData.monthly_kwh,
                    supplier_name: ocr.supplierName || formData.supplier_name,
                    total_amount: ocr.totalAmount || formData.total_amount,
                    billing_date_from: ocr.billingPeriod.normalized.start_date || formData.billing_date_from,
                    billing_date_to: ocr.billingPeriod.normalized.end_date || formData.billing_date_to,
                };

                setParsedData(parsed);
            }

            console.log("Final bill data:", mergedData);
            // TODO: Send mergedData to your backend or save it

        } catch (err) {
            console.error("Upload failed:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="felx-1 gap-2  min-h-screen bg-gray-50 flex items-center justify-center p-6">
            <form
                onSubmit={handleSubmit}
                className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md space-y-6 border border-gray-100 animate-fade-in"
            >
                <h2 className="text-2xl font-semibold text-emerald-700 text-center">
                    ⚡ Strom Sense
                </h2>
                {loading ? <SpaceIcon>Loading </SpaceIcon> : null}
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-600">Monthly kWh</label>
                        <input
                            type="number"
                            name="monthly_kwh"
                            value={formData.monthly_kwh}
                            onChange={handleChange}
                            className="w-full mt-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                            placeholder="Enter your monthly consumption"
                            required={!selectedFile}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-600">Billing Date From</label>
                            <input
                                type="date"
                                name="billing_date_from"
                                value={formData.billing_date_from}
                                onChange={handleChange}
                                className="w-full mt-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                                required={!selectedFile}

                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-600">Billing Date To</label>
                            <input
                                type="date"
                                name="billing_date_to"
                                value={formData.billing_date_to}
                                onChange={handleChange}
                                className="w-full mt-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                                required={!selectedFile}

                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-600">Supplier Name</label>
                        <input
                            type="text"
                            name="supplier_name"
                            value={formData.supplier_name}
                            onChange={handleChange}
                            className="w-full mt-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                            placeholder="e.g. Green Planet Energy"
                            required={!selectedFile}

                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-600">Total Amount (€)</label>
                        <input
                            type="number"
                            step="0.01"
                            name="total_amount"
                            value={formData.total_amount}
                            onChange={handleChange}
                            className="w-full mt-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                            placeholder="Enter total bill amount"
                            required={!selectedFile}

                        />
                    </div>
                </div>

                <button
                    type="submit"
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 rounded-lg transition-all duration-300 shadow-md hover:shadow-lg"
                >
                    Submit
                </button>
                <FileUpload onFileSelect={handleFileSelect} />
            </form>
            {parsedData &&
                <VerificationPanel data={parsedData} onSave={handleSave} />
            }


        </div>
    );
}
export default BillInput;
