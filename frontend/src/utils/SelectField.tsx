interface SelectFieldProps {
    label: string;
    name: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    options: string[];
    required?: boolean;
}

export const SelectField: React.FC<SelectFieldProps> = ({
    label,
    name,
    value,
    onChange,
    options,
    required,
}) => (
    <div>
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        <select
            name={name}
            value={value}
            onChange={onChange}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            required={required}
        >
            <option value="">Select...</option>
            {options.map((opt) => (
                <option key={opt} value={opt.toLowerCase().replace(" ", "_")}>
                    {opt}
                </option>
            ))}
        </select>
    </div>
);
