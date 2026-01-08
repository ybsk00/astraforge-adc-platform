import ComponentList from '@/components/catalog/ComponentList';

export const metadata = {
    title: 'Catalog - ADC Platform',
    description: 'Manage ADC component catalog',
};

export default function CatalogPage() {
    return (
        <main className="min-h-screen bg-gray-50">
            <ComponentList />
        </main>
    );
}
