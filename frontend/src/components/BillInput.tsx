
import { useState } from "react";
import { InputField } from "../utils/InputField";
import { SelectField } from "../utils/SelectField";
import FileUpload from "../components/FileUpload";

// 1. Define interface for form data
interface BillFormData {
    squareMeters: number | "";
    numOccupants: number | "";
    heatingType: string;
    monthlyKwh: number | "";
}

const BillInputPage: React.FC = () => {
    // 2. Initialize state with typed interface
    const [formData, setFormData] = useState<BillFormData>({
        squareMeters: "",
        numOccupants: "",
        heatingType: "",
        monthlyKwh: "",
    });

    // 3. Handle input changes
    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;

        setFormData((prev) => ({
            ...prev,
            [name]: name === "squareMeters" || name === "numOccupants" || name === "monthlyKwh"
                ? value === "" ? "" : parseInt(value)
                : value,
        }));
    };

    // 4. Handle form submission
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        console.log("Form submitted:", formData);
        // TODO: Connect to backend API
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-green-50 to-white flex items-center justify-center px-4 py-12">
            <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl p-8 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800 text-center mb-6">
                    ⚡ WattWise – Bill Input
                </h1>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <InputField
                            label="Living Area (m²)"
                            name="squareMeters"
                            value={formData.squareMeters}
                            onChange={handleChange}
                            placeholder="e.g. 85"
                            required
                        />
                        <InputField
                            label="Occupants"
                            name="numOccupants"
                            value={formData.numOccupants}
                            onChange={handleChange}
                            placeholder="e.g. 3"
                            required
                        />
                    </div>

                    <SelectField
                        label="Heating Type"
                        name="heatingType"
                        value={formData.heatingType}
                        onChange={handleChange}
                        options={["Electric", "Gas", "District Heating", "Heat Pump"]}
                        required
                    />

                    <InputField
                        label="Monthly Consumption (kWh)"
                        name="monthlyKwh"
                        value={formData.monthlyKwh}
                        onChange={handleChange}
                        placeholder="e.g. 320"
                        required
                    />

                    <button
                        type="submit"
                        className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg hover:bg-green-700 transition duration-200"
                    >
                        🔍 Analyze My Usage
                    </button>
                </form>
                <div className="mt-2">
                    <FileUpload onFileSelect={(file) => console.log("Selected file:", file)} />
                </div>
            </div>
        </main>
    );
};

export default BillInputPage;
