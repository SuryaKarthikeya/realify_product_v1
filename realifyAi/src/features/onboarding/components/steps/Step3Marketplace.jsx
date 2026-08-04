import Step5Connect from "./Step5Connect";

function Step3Marketplace() {
  return (
    <div className="max-w-xl mx-auto anim-fade-in w-full pb-6">
      <div className="mb-6 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Connect Your Data</h2>
        <p className="text-gray-500 text-sm">Sync your sales data automatically from the world's leading platforms.</p>
      </div>

      <div className="mt-2">
        <Step5Connect />
      </div>
    </div>
  );
}

export default Step3Marketplace;
