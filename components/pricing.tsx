"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, CreditCard, Smartphone, Building2, X, Zap } from "lucide-react"
import { authManager } from "@/lib/auth"

interface PricingProps {
  onClose: () => void
  currentPlan?: string
  onUpgrade: () => void
}

export function Pricing({ onClose, currentPlan = "free", onUpgrade }: PricingProps) {
  const [selectedPlan, setSelectedPlan] = useState("")
  const [paymentMethod, setPaymentMethod] = useState("upi")
  const [loading, setLoading] = useState(false)
  const [pricingModel, setPricingModel] = useState<"subscription" | "payperuse">("subscription")
  const [error, setError] = useState("")

  const plans = [
    {
      id: "free",
      name: "Free",
      price: "₹0",
      period: "forever",
      description: "Perfect for trying out the platform",
      features: [
        "10 blogs per month",
        "1 WordPress account",
        "Basic AI image generation",
        "Email support",
        "Standard templates",
      ],
      limitations: ["Limited to 10 blogs total", "Single WordPress account only", "Basic support only"],
      popular: false,
      current: currentPlan === "free",
    },
    {
      id: "starter",
      name: "Starter",
      price: "₹499",
      period: "month",
      description: "Great for small businesses and bloggers",
      features: [
        "100 blogs per month",
        "3 WordPress accounts",
        "Advanced AI image generation",
        "Priority email support",
        "Premium templates",
        "SEO optimization",
        "Analytics dashboard",
      ],
      popular: true,
      current: currentPlan === "starter",
    },
    {
      id: "professional",
      name: "Professional",
      price: "₹1,499",
      period: "month",
      description: "Perfect for agencies and content creators",
      features: [
        "500 blogs per month",
        "10 WordPress accounts",
        "Custom AI models",
        "Phone & email support",
        "Custom templates",
        "Advanced SEO tools",
        "Team collaboration",
        "API access",
      ],
      popular: false,
      current: currentPlan === "professional",
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: "₹4,999",
      period: "month",
      description: "For large organizations with custom needs",
      features: [
        "Unlimited blogs",
        "Unlimited WordPress accounts",
        "Custom AI training",
        "Dedicated support manager",
        "White-label solution",
        "Advanced analytics",
        "Custom integrations",
        "SLA guarantee",
      ],
      popular: false,
      current: currentPlan === "enterprise",
    },
  ]

  const payPerBlogOptions = [
    {
      id: "single",
      name: "Single Blog",
      price: "₹75",
      description: "Perfect for one-time blog needs",
      features: [
        "1 high-quality blog post",
        "SEO optimized content",
        "AI image generation",
        "WordPress publishing",
        "Basic support",
      ],
      popular: false,
    },
    {
      id: "pack5",
      name: "5 Blog Pack",
      price: "₹299",
      originalPrice: "₹375",
      description: "Save ₹76 with this pack",
      features: [
        "5 high-quality blog posts",
        "SEO optimized content",
        "AI image generation",
        "WordPress publishing",
        "Priority support",
        "Content calendar",
      ],
      popular: true,
    },
    {
      id: "pack10",
      name: "10 Blog Pack",
      price: "₹549",
      originalPrice: "₹750",
      description: "Save ₹201 with this pack",
      features: [
        "10 high-quality blog posts",
        "SEO optimized content",
        "AI image generation",
        "WordPress publishing",
        "Priority support",
        "Content calendar",
        "Analytics tracking",
      ],
      popular: false,
    },
    {
      id: "pack25",
      name: "25 Blog Pack",
      price: "₹1,199",
      originalPrice: "₹1,875",
      description: "Save ₹676 with this pack",
      features: [
        "25 high-quality blog posts",
        "SEO optimized content",
        "AI image generation",
        "WordPress publishing",
        "Priority support",
        "Content calendar",
        "Analytics tracking",
        "Custom templates",
      ],
      popular: false,
    },
  ]

  const paymentMethods = [
    { id: "upi", name: "UPI", icon: Smartphone, description: "Pay with any UPI app" },
    { id: "card", name: "Credit/Debit Card", icon: CreditCard, description: "Visa, Mastercard, RuPay" },
    { id: "netbanking", name: "Net Banking", icon: Building2, description: "All major banks supported" },
  ]

  const handleUpgrade = async () => {
    if (!selectedPlan) return

    setLoading(true)
    setError("")

    try {
      if (pricingModel === "subscription") {
        const result = await authManager.updateSubscription(
          selectedPlan as "starter" | "professional" | "enterprise",
          paymentMethod,
        )

        if (result.success) {
          onUpgrade()
          onClose()
        } else {
          setError(result.error || "Payment failed")
        }
      } else {
        // Handle pay-per-blog purchases
        await new Promise((resolve) => setTimeout(resolve, 2000))
        const option = payPerBlogOptions.find((p) => p.id === selectedPlan)
        alert(`Payment successful! Purchased ${option?.name}`)
        onClose()
      }
    } catch (error) {
      setError("Payment processing failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Choose Your Plan</h2>
              <p className="text-gray-600 mt-1">Upgrade to unlock more features and generate unlimited blogs</p>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-gray-600">
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center justify-center mt-6">
            <div className="bg-gray-100 p-1 rounded-lg flex">
              <button
                onClick={() => setPricingModel("subscription")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  pricingModel === "subscription"
                    ? "bg-white text-indigo-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Monthly Plans
              </button>
              <button
                onClick={() => setPricingModel("payperuse")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  pricingModel === "payperuse"
                    ? "bg-white text-indigo-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <Zap className="h-4 w-4 inline mr-1" />
                Pay Per Blog
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {pricingModel === "subscription" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {plans.map((plan) => (
                <Card
                  key={plan.id}
                  className={`relative cursor-pointer transition-all ${
                    selectedPlan === plan.id ? "ring-2 ring-indigo-500 shadow-lg" : "hover:shadow-md"
                  } ${plan.current ? "opacity-60" : ""}`}
                  onClick={() => !plan.current && setSelectedPlan(plan.id)}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-indigo-500 text-white px-3 py-1">Most Popular</Badge>
                    </div>
                  )}
                  {plan.current && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-green-500 text-white px-3 py-1">Current Plan</Badge>
                    </div>
                  )}

                  <CardHeader className="text-center pb-4">
                    <CardTitle className="text-lg font-semibold">{plan.name}</CardTitle>
                    <div className="mt-2">
                      <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                      {plan.period !== "forever" && <span className="text-gray-600">/{plan.period}</span>}
                    </div>
                    <CardDescription className="text-sm">{plan.description}</CardDescription>
                  </CardHeader>

                  <CardContent>
                    <ul className="space-y-2 mb-4">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {plan.limitations && (
                      <div className="border-t pt-3 mt-3">
                        <p className="text-xs font-medium text-gray-500 mb-2">Limitations:</p>
                        <ul className="space-y-1">
                          {plan.limitations.map((limitation, index) => (
                            <li key={index} className="text-xs text-gray-500">
                              • {limitation}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div>
              <div className="text-center mb-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Pay Per Blog</h3>
                <p className="text-gray-600">Perfect for occasional blog generation without monthly commitments</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {payPerBlogOptions.map((option) => (
                  <Card
                    key={option.id}
                    className={`relative cursor-pointer transition-all ${
                      selectedPlan === option.id ? "ring-2 ring-indigo-500 shadow-lg" : "hover:shadow-md"
                    }`}
                    onClick={() => setSelectedPlan(option.id)}
                  >
                    {option.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <Badge className="bg-orange-500 text-white px-3 py-1">Best Value</Badge>
                      </div>
                    )}

                    <CardHeader className="text-center pb-4">
                      <CardTitle className="text-lg font-semibold">{option.name}</CardTitle>
                      <div className="mt-2">
                        <span className="text-3xl font-bold text-gray-900">{option.price}</span>
                        {option.originalPrice && (
                          <div className="text-sm text-gray-500 line-through">{option.originalPrice}</div>
                        )}
                      </div>
                      <CardDescription className="text-sm">{option.description}</CardDescription>
                    </CardHeader>

                    <CardContent>
                      <ul className="space-y-2">
                        {option.features.map((feature, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {selectedPlan && selectedPlan !== "free" && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">Payment Method</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {paymentMethods.map((method) => (
                  <Card
                    key={method.id}
                    className={`cursor-pointer transition-all ${
                      paymentMethod === method.id ? "ring-2 ring-indigo-500 bg-indigo-50" : "hover:shadow-md"
                    }`}
                    onClick={() => setPaymentMethod(method.id)}
                  >
                    <CardContent className="p-4 text-center">
                      <method.icon className="h-8 w-8 mx-auto mb-2 text-indigo-600" />
                      <h4 className="font-medium text-sm">{method.name}</h4>
                      <p className="text-xs text-gray-500 mt-1">{method.description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded mb-4">{error}</p>}

              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  <p>✓ Secure payment powered by Razorpay</p>
                  <p>✓ {pricingModel === "subscription" ? "7-day money-back guarantee" : "Instant blog delivery"}</p>
                </div>
                <Button
                  onClick={handleUpgrade}
                  disabled={loading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-2"
                >
                  {loading
                    ? "Processing..."
                    : pricingModel === "subscription"
                      ? `Upgrade to ${plans.find((p) => p.id === selectedPlan)?.name}`
                      : `Purchase ${payPerBlogOptions.find((p) => p.id === selectedPlan)?.name}`}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
