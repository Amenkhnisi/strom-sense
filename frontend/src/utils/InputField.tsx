interface InputFieldProps {
    label: string;
    name: string;
    value: number | "";
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    placeholder?: string;
    required?: boolean;
}

export const InputField: React.FC<InputFieldProps> = ({
    label,
    name,
    value,
    onChange,
    placeholder,
    required,
}) => (
    <div>
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        <input
            type="number"
            name={name}
            value={value}
            onChange={onChange}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder={placeholder}
            required={required}
        />
    </div>
);
