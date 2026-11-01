import { RecipeScreen } from "@/components/screens/RecipeScreen";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <RecipeScreen id={id} />;
}
